import pandas as pd
import streamlit as st
from src.processing.column_detection import find_columns, scrub_raw_dataframe
from src.processing.categorization import get_category_for_sales, get_sub_category_for_sales
from src.utils.product import get_base_product_name, get_size_from_name
from src.utils.logging import log_system_event


def process_data(df, selected_cols):
    """Main entry point for initial data processing. Returns granular sanitized data + aggregates."""
    df_standard, timeframe = prepare_granular_data(df, selected_cols)
    if df_standard.empty:
        return None, None, None, "", {}
    drill, summ, top, basket = aggregate_data(df_standard, selected_cols)
    return drill, summ, top, timeframe, basket

def prepare_granular_data(df, selected_cols):
    """Sanitizes and prepares granular columns with unified internal names."""
    try:
        df = df.copy()
        df = scrub_raw_dataframe(df)

        if df.empty:
            return df, ""

        # Mapping to Standard Names for easier internal logic
        df["Product Name"] = df[selected_cols["name"]].fillna("Unknown Product").astype(str)
        df = df[~df["Product Name"].str.contains("Choose Any", case=False, na=False)]

        df["Item Cost"] = pd.to_numeric(df[selected_cols["cost"]], errors="coerce").fillna(0)
        df["Quantity"] = pd.to_numeric(df[selected_cols["qty"]], errors="coerce").fillna(0)

        # v10.4 Standardized SKU support
        if "sku" in selected_cols and selected_cols["sku"] in df.columns:
             df["SKU"] = df[selected_cols["sku"]].fillna("N/A").astype(str)
        else:
             df["SKU"] = "N/A"


        timeframe_suffix = ""
        if "date" in selected_cols and selected_cols["date"] in df.columns:
            try:
                df["Date"] = pd.to_datetime(df[selected_cols["date"]], errors="coerce")
                dates_valid = df["Date"].dropna()
                if not dates_valid.empty:
                    # v10.2 Strip timezone for easier Streamlit widget comparison
                    df["Date"] = df["Date"].dt.tz_localize(None)

                    if dates_valid.dt.to_period("M").nunique() == 1:
                        timeframe_suffix = dates_valid.iloc[0].strftime("%B_%Y")
                    else:
                        timeframe_suffix = f"{dates_valid.min().strftime('%d%b')}_to_{dates_valid.max().strftime('%d%b_%y')}"
            except Exception:
                non_null = df[selected_cols["date"]].dropna()
                val = str(non_null.iloc[0]) if not non_null.empty else ""
                timeframe_suffix = val.replace("/", "-").replace(" ", "_")[:20]


        if (df["Quantity"] < 0).any():
            log_system_event("DATA_ISSUE", "Found negative quantities, converted to 0.")
            df.loc[df["Quantity"] < 0, "Quantity"] = 0

        # Optimized Categorization (v14.0)
        unique_names = df["Product Name"].unique()
        name_cat_map = {name: get_category_for_sales(name) for name in unique_names}
        df["Category"] = df["Product Name"].map(name_cat_map)

        # v11.7 Sub-Category Extraction
        df["Sub-Category"] = df.apply(lambda r: get_sub_category_for_sales(r["Product Name"], r["Category"]), axis=1)

        # v10.6 Size Extraction
        df["Size"] = df["Product Name"].apply(get_size_from_name)

        # v11.4 High-Density Filter Intelligence
        df["Clean_Product"] = df["Product Name"].apply(get_base_product_name)
        df["Filter_Identity"] = df["Clean_Product"] + " [" + df["SKU"].astype(str) + "]"

        df["Total Amount"] = df["Item Cost"] * df["Quantity"]


        # Ensure Order Status and other operational columns are present
        if "Order Status" not in df.columns:
            # Try to map status if not present (useful for manual uploads)
            status_col = find_columns(df).get("status")
            if status_col:
                df["Order Status"] = df[status_col].fillna("completed").astype(str).str.lower()
            else:
                df["Order Status"] = "completed"

        return df, timeframe_suffix
    except Exception as e:
        log_system_event("PREPARE_ERROR", str(e))
        return pd.DataFrame(), ""

def aggregate_data(df, selected_cols):
    """Generates dashboard aggregates from granular standardized data."""
    try:
        # v11.7 Grouping by Category + Sub-Category for granular reports
        group_keys = ["Category"]
        if "Sub-Category" in df.columns:
            group_keys.append("Sub-Category")

        summary = (
            df.groupby(group_keys)
            .agg({"Quantity": "sum", "Total Amount": "sum"})
            .reset_index()
        )
        if "Sub-Category" in summary.columns:
            summary.columns = ["Category", "Sub-Category", "Total Qty", "Total Amount"]
        else:
            summary.columns = ["Category", "Total Qty", "Total Amount"]

        total_rev = summary["Total Amount"].sum()
        total_qty = summary["Total Qty"].sum()
        if total_rev > 0:
            summary["Revenue Share (%)"] = (summary["Total Amount"] / total_rev * 100).round(2)
        if total_qty > 0:
            summary["Quantity Share (%)"] = (summary["Total Qty"] / total_qty * 100).round(2)

        drilldown = (
            df.groupby(["Category", "Sub-Category", "Item Cost"])
            .agg({"Quantity": "sum", "Total Amount": "sum"})
            .reset_index()
        )
        drilldown.columns = ["Category", "Sub-Category", "Price (TK)", "Total Qty", "Total Amount"]

        top_items = (
            df.groupby(["Product Name", "SKU"])
            .agg({"Quantity": "sum", "Total Amount": "sum", "Category": "first", "Sub-Category": "first"})
            .reset_index()
        )
        top_items.columns = ["Product Name", "SKU", "Total Qty", "Total Amount", "Category", "Sub-Category"]
        top_items = top_items.sort_values("Total Amount", ascending=False)

        basket_metrics = {"avg_basket_qty": 0, "avg_basket_value": 0, "total_orders": 0}
        group_cols = []
        if "order_id" in selected_cols and selected_cols["order_id"] in df.columns:
            group_cols.append(selected_cols["order_id"])
        elif "Order ID" in df.columns:
            group_cols.append("Order ID")

        if "phone" in selected_cols and selected_cols["phone"] in df.columns:
            group_cols.append(selected_cols["phone"])
        elif "Phone (Billing)" in df.columns:
            group_cols.append("Phone (Billing)")

        if group_cols:
            order_groups = df.groupby(group_cols).agg({
                "Quantity": "sum",
                "Total Amount": "sum",
                "Product Name": "count" # Items per order
            })
            basket_metrics["avg_basket_qty"] = order_groups["Quantity"].mean()
            basket_metrics["avg_basket_value"] = order_groups["Total Amount"].mean()
            basket_metrics["total_orders"] = len(order_groups)

            # 专业 DA: Attachment Rate Calculation
            # % of orders with more than 1 unique item
            multi_item_orders = len(order_groups[order_groups["Product Name"] > 1])
            basket_metrics["attachment_rate"] = (multi_item_orders / len(order_groups) * 100) if len(order_groups) > 0 else 0

        return drilldown, summary, top_items, basket_metrics
    except Exception as e:
        log_system_event("AGGREGATE_ERROR", str(e))
        return None, None, None, {}

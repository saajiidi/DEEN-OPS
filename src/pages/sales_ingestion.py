import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.components.widgets import render_action_bar, render_reset_confirm, section_card
from src.processing.column_detection import find_columns
from src.processing.data_processing import prepare_granular_data, aggregate_data
from src.pages.dashboard_output import render_dashboard_output
from src.services.woocommerce.client import load_from_woocommerce
from src.utils.file_io import read_sales_file
from src.utils.logging import log_system_event
from src.utils.snapshots import load_sales_snapshot, save_sales_snapshot


def render_manual_tab():
    def _reset_manual_state():
        st.session_state.manual_generate = False
        st.session_state.manual_df = None

    # v11.3 State Enforcement: Prioritize Ingestion UI over Live defaults
    st.session_state["manual_tab_active"] = True
    st.session_state["wc_sync_mode"] = "Custom Range"

    # Initialize default 7-day range if not present
    if "ingest_range" not in st.session_state:
        st.session_state.ingest_range = ((datetime.now() - timedelta(days=30)).date(), datetime.now().date())

    render_reset_confirm("Sales Data Ingestion", "manual", _reset_manual_state)

    st.info("\U0001f4ca Consolidate and analyze sales data. WooCommerce pull is active by default.")

    # v10.7 Auto-Load Intelligence with Snapshot Fallback
    if st.session_state.get("manual_df") is None and not st.session_state.get("manual_autoload_attempted", False):
        st.session_state["manual_autoload_attempted"] = True

        snap_df = load_sales_snapshot()
        if snap_df is not None:
            st.session_state.manual_df = snap_df
            st.session_state.manual_source_name = "Last_Synced_Snapshot (30 Days)"
            st.session_state["wc_sync_mode"] = "Custom Range"
            st.toast("\u26a1 Loaded Sales from Snapshot")
            st.rerun()
        else:
            # 2. If no snapshot, run API load
            with st.spinner("\U0001f680 Initial API sync (Last 30 Days)..."):
                try:
                    e_d = datetime.now().date()
                    s_d = e_d - timedelta(days=30)
                    st.session_state["wc_sync_mode"] = "Custom Range"
                    st.session_state["wc_sync_start_date"] = s_d
                    st.session_state["wc_sync_start_time"] = datetime.strptime("00:00", "%H:%M").time()
                    st.session_state["wc_sync_end_date"] = e_d
                    st.session_state["wc_sync_end_time"] = datetime.strptime("23:59", "%H:%M").time()

                    wc_res = load_from_woocommerce()
                    df_res = wc_res["df_to_return"]
                    src_res = wc_res["sync_desc"]
                    if not df_res.empty:
                        st.session_state.manual_df = df_res
                        st.session_state.manual_source_name = src_res
                        save_sales_snapshot(df_res)
                        st.toast("\u2705 API Sync Complete!")
                        st.rerun()
                except Exception:
                    pass


    # v11.3 Sync State
    df = st.session_state.get("manual_df")
    source_name = st.session_state.get("manual_source_name", "")

    # Optional Sources Expander
    with st.expander("\U0001f4e4 Optional: External Source (Upload / URL)"):
        uploaded_file = st.file_uploader("\U0001f4c2 Drag and drop sales file", type=["xlsx", "csv"], key="manual_uploader_v2")
        if uploaded_file:
            df_up = read_sales_file(uploaded_file, uploaded_file.name)
            if df_up is not None:
                st.session_state.manual_df = df_up
                st.session_state.manual_source_name = uploaded_file.name
                df = df_up
                source_name = uploaded_file.name

        url_input = st.text_input("\U0001f310 Or paste a public CSV/XLSX URL", key="manual_url_input")
        if url_input and st.button("Fetch from URL", use_container_width=True, type="secondary", key="manual_url_fetch"):
            try:
                from src.utils.url_fetch import fetch_dataframe_from_url
                with st.spinner("Fetching from URL..."):
                    df_url = fetch_dataframe_from_url(url_input)
                    st.session_state.manual_df = df_url
                    st.session_state.manual_source_name = "URL_Import"
                    df = df_url
                    source_name = "URL_Import"
                    st.success(f"Loaded {len(df_url)} rows from URL!")
            except Exception as e:
                st.error(f"URL fetch failed: {e}")

        if st.session_state.get("manual_df") is not None:
            df = st.session_state.manual_df
            source_name = st.session_state.get("manual_source_name", "WooCommerce_Custom_Pull")

    if df is None:
        # v11.3 Call unified dashboard with None to show ingestion expander
        render_dashboard_output(None, None, None, None, None, "None", granular_df=None)
        return

    try:
        # v10.7+ Direct Intelligence (Bypass mapping for WooCommerce and Snapshots)
        if "WooCommerce" in str(source_name) or "Snapshot" in str(source_name):
            # v11.4 Fix: WooCommerce fetch produces 'Order Date', ensure mapping aligns
            final_mapping = {
                "name": "Item Name",
                "cost": "Item Cost",
                "qty": "Quantity",
                "date": "Order Date" if "Date" not in df.columns else "Date",
                "order_id": "Order Number",
                "phone": "Phone (Billing)",
                "sku": "SKU"
            }
            df_standard, timeframe = prepare_granular_data(df, final_mapping)
            if not df_standard.empty:
                drill, summ, top, basket = aggregate_data(df_standard, final_mapping)
                # v10.9 Fix: Pass df_standard as granular_df to enable filters and rendering
                render_dashboard_output(drill, summ, top, timeframe, basket, source_name, granular_df=df_standard)
            return

        st.caption(f"Active Data Source: {source_name}")
        auto_cols = find_columns(df)
        all_cols = list(df.columns)

        section_card(
            "Column Mapping",
            "Detected columns are prefilled. Verify before generating dashboard output.",
        )

        def get_col_idx(key):
            if key in auto_cols and auto_cols[key] in all_cols:
                return all_cols.index(auto_cols[key])
            return 0

        mapped_name = st.selectbox(
            "Product Name", all_cols, index=get_col_idx("name"), key="manual_name"
        )
        mapped_cost = st.selectbox(
            "Price/Cost", all_cols, index=get_col_idx("cost"), key="manual_cost"
        )
        mapped_qty = st.selectbox(
            "Quantity", all_cols, index=get_col_idx("qty"), key="manual_qty"
        )
        mapped_date = st.selectbox(
            "Date (Optional)",
            ["None"] + all_cols,
            index=get_col_idx("date") + 1 if "date" in auto_cols else 0,
            key="manual_date",
        )
        mapped_order = st.selectbox(
            "Order ID (Optional)",
            ["None"] + all_cols,
            index=get_col_idx("order_id") + 1 if "order_id" in auto_cols else 0,
            key="manual_order",
        )
        mapped_phone = st.selectbox(
            "Phone (Optional)",
            ["None"] + all_cols,
            index=get_col_idx("phone") + 1 if "phone" in auto_cols else 0,
            key="manual_phone",
        )
        mapped_sku = st.selectbox(
             "SKU (Optional)",
             ["None"] + all_cols,
             index=get_col_idx("sku") + 1 if "sku" in auto_cols else 0,
             key="manual_sku"
        )

        final_mapping = {
            "name": mapped_name,
            "cost": mapped_cost,
            "qty": mapped_qty,
            "date": mapped_date if mapped_date != "None" else None,
            "order_id": mapped_order if mapped_order != "None" else None,
            "phone": mapped_phone if mapped_phone != "None" else None,
            "sku": mapped_sku if mapped_sku != "None" else None,
        }


        with st.expander("Search Raw Data"):
            search = st.text_input("Product search...", key="manual_search")
            if search:
                st.dataframe(
                    df[
                        df[mapped_name]
                        .astype(str)
                        .str.contains(search, case=False, na=False)
                    ],
                    use_container_width=True,
                )
            else:
                st.dataframe(df.head(10), use_container_width=True)

        generate_clicked, _ = render_action_bar("Generate dashboard", "manual_generate")
        if generate_clicked:
            df_standard, timeframe = prepare_granular_data(df, final_mapping)
            if not df_standard.empty:
                drill, summ, top, basket = aggregate_data(df_standard, final_mapping)
                manual_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                render_dashboard_output(
                    drill,
                    summ,
                    top,
                    timeframe,
                    basket,
                    source_name,
                    manual_updated,
                    granular_df=df_standard
                )


    except Exception as e:
        log_system_event("FILE_ERROR", str(e))
        st.error(f"File error: {e}")

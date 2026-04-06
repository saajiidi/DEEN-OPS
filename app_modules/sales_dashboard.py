import re
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import streamlit.components.v1 as components
import base64
import requests
from datetime import datetime, timedelta, timezone
from io import BytesIO
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlparse
from requests.auth import HTTPBasicAuth
from app_modules.ui_components import (
    section_card,
    render_action_bar,
    render_reset_confirm,
)


def render_snapshot_button(marker_id="snapshot-target"):
    """Capture and download dashboard area snapshot as PNG."""
    html_code = """
    <div style="text-align:right; margin:6px 0 2px 0;">
      <button onclick="captureDashboard()" style="
          background:#1d4ed8; color:#fff; border:none; border-radius:8px;
          padding:7px 12px; font-size:13px; font-weight:600; cursor:pointer;">
          Save Snapshot
      </button>
    </div>
    <script>
    function captureDashboard() {
      const marker = window.parent.document.getElementById('__MARKER__');
      let target = null;
      if (marker) {
        target = marker.closest('[data-testid="stVerticalBlock"]');
      }
      if (!target) {
        target = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
      }
      if (!target) return;

      const doCapture = () => {
        const originalPadding = target.style.padding;
        const originalBackground = target.style.backgroundColor;
        const originalBorderRadius = target.style.borderRadius;
        const appBg = window.parent.getComputedStyle(window.parent.document.body).backgroundColor || '#0f172a';

        // Add breathing room so left edge does not feel cramped in snapshot.
        target.style.padding = '18px 22px 18px 30px';
        target.style.backgroundColor = appBg;
        target.style.borderRadius = '12px';

        window.parent.html2canvas(target, {useCORS: true, scale: 2, backgroundColor: appBg})
          .then((canvas) => {
            target.style.padding = originalPadding;
            target.style.backgroundColor = originalBackground;
            target.style.borderRadius = originalBorderRadius;
            const a = window.parent.document.createElement('a');
            a.download = 'dashboard_snapshot.png';
            a.href = canvas.toDataURL('image/png');
            a.click();
          })
          .catch(() => {
            target.style.padding = originalPadding;
            target.style.backgroundColor = originalBackground;
            target.style.borderRadius = originalBorderRadius;
          });
      };

      if (!window.parent.html2canvas) {
        const script = window.parent.document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        script.onload = doCapture;
        window.parent.document.head.appendChild(script);
      } else {
        doCapture();
      }
    }
    </script>
    """.replace("__MARKER__", marker_id)
    components.html(html_code, height=44)


# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FEEDBACK_DIR = os.path.join(DATA_DIR, "feedback")
INCOMING_DIR = os.path.join(DATA_DIR, "incoming")
DEFAULT_GSHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOiRkybNzMNvEaLxSFsX0nGIiM07BbNVsBbsX1dG8AmGOmSu8baPrVYL0cOqoYN4tRWUj1UjUbH1Ij/pub?gid=2118542421&single=true&output=csv"
os.makedirs(FEEDBACK_DIR, exist_ok=True)
os.makedirs(INCOMING_DIR, exist_ok=True)


def log_system_event(event_type, details):
    """Logs errors or system events to a JSON file for further analysis."""
    log_file = os.path.join(FEEDBACK_DIR, "system_logs.json")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = {"timestamp": timestamp, "type": event_type, "details": details}

    try:
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)

        logs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        print(f"Logging failed: {e}")


def save_user_feedback(comment):
    """Saves user comments to a feedback file."""
    feedback_file = os.path.join(FEEDBACK_DIR, "user_feedback.json")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    feedback_entry = {"timestamp": timestamp, "comment": comment}

    try:
        data = []
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        data.append(feedback_entry)
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False


def get_setting(key, default=None):
    """Reads setting from Streamlit secrets first, then env var."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


def get_gcp_service_account_info():
    """Returns service account info from st.secrets or env JSON."""
    try:
        if "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass

    raw = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            raise ValueError(f"Invalid GCP_SERVICE_ACCOUNT_JSON: {e}")

    return None


def get_category(name):
    """Categorizes products based on detailed keywords and logic (merged from analytics)."""
    name_str = str(name).lower()

    # Detailed lambda-based rules for high-precision categorization
    stock_rules = {
        "Jeans Slim Fit": lambda n: "jeans" in n and "slim fit" in n,
        "Jeans Regular Fit": lambda n: "jeans" in n and "regular fit" in n,
        "Jeans Straight Fit": lambda n: "jeans" in n and "straight fit" in n,
        "Panjabi": lambda n: "panjabi" in n,
        "Active Wear": lambda n: "active wear" in n,
        "T-shirt Basic Full": lambda n: "t-shirt" in n and "full sleeve" in n,
        "T-shirt Drop-Shoulder": lambda n: "t-shirt" in n and ("drop-shoulder" in n or "drop shoulder" in n),
        "T-shirt Basic Half": lambda n: "t-shirt" in n and not ("full sleeve" in n or "drop-shoulder" in n or "drop shoulder" in n),
        "Sweatshirt": lambda n: "sweatshirt" in n,
        "Turtle-Neck": lambda n: "turtle-neck" in n or "turtleneck" in n,
        "Tank-Top": lambda n: "tank-top" in n or "tank top" in n,
        "Trousers Cotton": lambda n: ("trouser" in n or "jogger" in n or "pant" in n) and ("twill" in n or "chino" in n or "cotton" in n),
        "Trousers Terry": lambda n: ("trouser" in n or "jogger" in n or "pant" in n) and "terry" in n,
        "Polo": lambda n: "polo" in n,
        "Kaftan Shirt": lambda n: "kaftan" in n,
        "Denim Shirt": lambda n: "denim" in n and "shirt" in n,
        "Flannel Shirt": lambda n: "flannel" in n and "shirt" in n,
        "Casual Shirt Full": lambda n: "shirt" in n and "full sleeve" in n and not any(k in n for k in ["denim", "flannel", "kaftan", "polo"]),
        "Casual Shirt Half": lambda n: "shirt" in n and not any(k in n for k in ["full sleeve", "denim", "flannel", "kaftan", "polo", "t-shirt"]),
        "Belt": lambda n: "belt" in n,
        "Wallet": lambda n: "wallet" in n,
        "Mask": lambda n: "mask" in n,
        "Water Bottle": lambda n: "water bottle" in n,
        "Boxer": lambda n: "boxer" in n,
    }

    # First try high-precision rules
    for cat, rule in stock_rules.items():
        if rule(name_str):
            return cat

    # Fallback to broader keyword matching
    def has_any(keywords, text):
        return any(re.search(rf"\b{re.escape(kw.lower())}\b", text, re.IGNORECASE) for kw in keywords)

    broader_cats = {
        "Leather Bag": ["bag", "backpack"],
        "Jersy": ["jersy"],
        "Jacket": ["jacket", "outerwear", "coat"],
        "Sweater": ["sweater", "cardigan", "knitwear"],
        "Passport Holder": ["passport holder"],
        "Cap": ["cap"],
    }

    for cat, keywords in broader_cats.items():
        if has_any(keywords, name_str):
            return cat

    return "Others"


@st.cache_data(show_spinner=False)
def find_columns(df):
    """Detects primary columns using exact and then partial matching."""
    mapping = {
        "name": [
            "item name",
            "product name",
            "product",
            "item",
            "title",
            "description",
            "name",
        ],
        "cost": [
            "item cost",
            "price",
            "unit price",
            "cost",
            "rate",
            "mrp",
            "selling price",
        ],
        "qty": ["quantity", "qty", "units", "sold", "count", "total quantity"],
        "date": ["date", "order date", "month", "time", "created at"],
        "order_id": [
            "order id",
            "order #",
            "invoice number",
            "invoice #",
            "order number",
            "transaction id",
            "id",
        ],
        "phone": [
            "phone",
            "contact",
            "mobile",
            "cell",
            "phone number",
            "customer phone",
        ],
    }

    found = {}
    actual_cols = [c.strip() for c in df.columns]
    lower_cols = [c.lower() for c in actual_cols]

    for key, aliases in mapping.items():
        for alias in aliases:
            if alias in lower_cols:
                idx = lower_cols.index(alias)
                found[key] = actual_cols[idx]
                break

    for key, aliases in mapping.items():
        if key not in found:
            for col, l_col in zip(actual_cols, lower_cols):
                if any(alias in l_col for alias in aliases):
                    found[key] = col
                    break

    return found


@st.cache_data(show_spinner=False)
def scrub_raw_dataframe(df):
    """Filters out dashboard analytics, empty rows, and summary tables from raw exports."""
    if df is None or df.empty:
        return df

    # 1. Drop completely empty rows
    df = df.dropna(how="all")

    # 2. Heuristic: If a row has extremely few non-null values compared to the max, it's likely a summary or title
    # We'll keep rows that have at least 30% of the columns filled
    min_threshold = max(1, int(len(df.columns) * 0.3))
    df = df.dropna(thresh=min_threshold)

    # 3. Filter out rows containing common summary keywords in any column
    summary_keywords = [
        "total",
        "grand total",
        "summary",
        "analytics",
        "chart",
        "metric",
    ]
    mask = (
        df.stack()
        .astype(str)
        .str.lower()
        .str.contains("|".join(summary_keywords))
        .unstack()
        .any(axis=1)
    )
    # Only drop if the row is mostly text (summary rows) - be careful not to drop product names with "total"
    # Actually, a better indicator of summary rows is that they are sparse.
    # Let's stick to sparsity and dropping based on ID if we have it later.

    return df


def process_data(df, selected_cols):
    """Processed data using validated user-selected or auto-detected columns."""
    try:
        df = df.copy()

        # Scrub dashboard analytics, pivot tables, and empty totals from live exports
        df = scrub_raw_dataframe(df)

        if df.empty:
            raise ValueError("Dataset is empty after stripping metrics/analytics rows.")

        df["Internal_Name"] = (
            df[selected_cols["name"]].fillna("Unknown Product").astype(str)
        )
        df = df[~df["Internal_Name"].str.contains("Choose Any", case=False, na=False)]

        df["Internal_Cost"] = pd.to_numeric(
            df[selected_cols["cost"]], errors="coerce"
        ).fillna(0)
        df["Internal_Qty"] = pd.to_numeric(
            df[selected_cols["qty"]], errors="coerce"
        ).fillna(0)

        timeframe_suffix = ""
        if "date" in selected_cols and selected_cols["date"] in df.columns:
            try:
                dates = pd.to_datetime(
                    df[selected_cols["date"]], errors="coerce"
                ).dropna()
                if not dates.empty:
                    if dates.dt.to_period("M").nunique() == 1:
                        timeframe_suffix = dates.iloc[0].strftime("%B_%Y")
                    else:
                        timeframe_suffix = f"{dates.min().strftime('%d%b')}_to_{dates.max().strftime('%d%b_%y')}"
            except Exception:
                non_null = df[selected_cols["date"]].dropna()
                val = str(non_null.iloc[0]) if not non_null.empty else ""
                timeframe_suffix = val.replace("/", "-").replace(" ", "_")[:20]

        if (df["Internal_Qty"] < 0).any():
            log_system_event("DATA_ISSUE", "Found negative quantities, converted to 0.")
            df.loc[df["Internal_Qty"] < 0, "Internal_Qty"] = 0

        df["Category"] = df["Internal_Name"].apply(get_category)
        df["Total Amount"] = df["Internal_Cost"] * df["Internal_Qty"]

        others = df[df["Category"] == "Others"]
        if len(others) > 0:
            log_system_event(
                "OTHERS_LOG",
                {
                    "count": len(others),
                    "samples": others["Internal_Name"].head(10).tolist(),
                },
            )

        summary = (
            df.groupby("Category")
            .agg({"Internal_Qty": "sum", "Total Amount": "sum"})
            .reset_index()
        )
        summary.columns = ["Category", "Total Qty", "Total Amount"]

        total_rev = summary["Total Amount"].sum()
        total_qty = summary["Total Qty"].sum()
        if total_rev > 0:
            summary["Revenue Share (%)"] = (
                summary["Total Amount"] / total_rev * 100
            ).round(2)
        if total_qty > 0:
            summary["Quantity Share (%)"] = (
                summary["Total Qty"] / total_qty * 100
            ).round(2)

        drilldown = (
            df.groupby(["Category", "Internal_Cost"])
            .agg({"Internal_Qty": "sum", "Total Amount": "sum"})
            .reset_index()
        )
        drilldown.columns = ["Category", "Price (TK)", "Total Qty", "Total Amount"]

        top_items = (
            df.groupby("Internal_Name")
            .agg({"Internal_Qty": "sum", "Total Amount": "sum", "Category": "first"})
            .reset_index()
        )
        top_items.columns = ["Product Name", "Total Qty", "Total Amount", "Category"]
        top_items = top_items.sort_values("Total Amount", ascending=False)

        basket_metrics = {"avg_basket_qty": 0, "avg_basket_value": 0, "total_orders": 0}
        group_cols = []
        if "order_id" in selected_cols and selected_cols["order_id"] in df.columns:
            group_cols.append(selected_cols["order_id"])
        if "phone" in selected_cols and selected_cols["phone"] in df.columns:
            group_cols.append(selected_cols["phone"])

        if group_cols:
            order_groups = df.groupby(group_cols).agg(
                {"Internal_Qty": "sum", "Total Amount": "sum"}
            )
            basket_metrics["avg_basket_qty"] = order_groups["Internal_Qty"].mean()
            basket_metrics["avg_basket_value"] = order_groups["Total Amount"].mean()
            basket_metrics["total_orders"] = len(order_groups)

        return drilldown, summary, top_items, timeframe_suffix, basket_metrics
    except Exception as e:
        log_system_event("CRASH", str(e))
        st.error(f"Error in calculation: {e}")
        return None, None, None, "", {}


@st.cache_data(show_spinner=False)
def read_sales_file(file_obj, file_name):
    """Reads CSV/XLSX from uploader, file path, or bytes buffer."""
    if str(file_name).lower().endswith(".csv"):
        return pd.read_csv(file_obj)
    return pd.read_excel(file_obj)


@st.cache_data(ttl=60, show_spinner=False)
def load_from_woocommerce():
    """Loads live data from WooCommerce REST API orders."""
    # Check for nested [woocommerce] in st.secrets (from secrets.toml)
    wc_info = {}
    try:
        wc_info = st.secrets.get("woocommerce", {})
    except Exception:
        pass

    # Support both nested [woocommerce] table and top-level keys/env vars
    wc_url = wc_info.get("store_url") or get_setting("WC_URL")
    wc_key = wc_info.get("consumer_key") or get_setting("WC_KEY")
    wc_secret = wc_info.get("consumer_secret") or get_setting("WC_SECRET")

    if not wc_url or not wc_key or not wc_secret:
        raise ValueError(
            "WooCommerce integration requires WC_URL, WC_KEY, and WC_SECRET (or [woocommerce] table in secrets.toml)."
        )

    # Unified WooCommerce API fetching with multi-page support
    endpoint = f"{wc_url.rstrip('/')}/wp-json/wc/v3/orders"
    rows = []
    
    try:
        from datetime import timezone, timedelta
        tz_bd = timezone(timedelta(hours=6))
        
        # Determine pulling window based on user selection in session state
        sync_mode = st.session_state.get("wc_sync_mode", "Operational Cycle")
        
        params = {
            "per_page": 100,
            "status": "processing,completed,shipped",
            "orderby": "date",
            "order": "desc"
        }

        def get_operational_sync_window(ref_time):
            # Thursday 5 PM to Saturday 5 PM is the weekend slot (Bangladesh)
            # anchor_5pm is 17:00 of the reference day
            anchor_5pm = ref_time.replace(hour=17, minute=0, second=0, microsecond=0)
            if ref_time >= anchor_5pm:
                start = anchor_5pm
            else:
                start = anchor_5pm - timedelta(days=1)
            
            # Weekend adjustment: Friday is covered by the Thu-Sat slot
            if start.weekday() == 4: # Friday
                start -= timedelta(days=1) # Back to Thu 17:00
            
            # Duration adjustment
            if start.weekday() == 3: # Thu 17:00
                end = start + timedelta(days=2) # To Sat 17:00
            else:
                end = start + timedelta(days=1)
                
            return start, end

        # Specialized Fetching Strategy for Operational Cycle
        if sync_mode == "Operational Cycle":
            now_bd = datetime.now(tz_bd)
            curr_start, curr_end = get_operational_sync_window(now_bd)
            prev_start, prev_end = get_operational_sync_window(curr_start - timedelta(seconds=1))
            st.session_state.wc_curr_slot = (curr_start, curr_end)
            st.session_state.wc_prev_slot = (prev_start, prev_end)
            
            # Request 1: All relevant statuses within the broad operational window
            # (since prev_start, to catch both current and previous slots)
            params["after"] = prev_start.isoformat()
            params["before"] = curr_end.isoformat()
            params["status"] = "processing,completed,shipped,on-hold,pending"
            
            # Fetch Batch 1 (Window based)
            def fetch_batch(p):
                b_rows = []
                page = 1
                while True:
                    r = requests.get(endpoint, params={**p, "page": page}, auth=HTTPBasicAuth(wc_key, wc_secret), timeout=15)
                    r.raise_for_status()
                    batch_data = r.json()
                    if not batch_data: break
                    for order in batch_data:
                        oid, d_val, status = order.get("id"), order.get("date_created"), order.get("status")
                        bill = order.get("billing", {})
                        c_name = f"{bill.get('first_name','')} {bill.get('last_name','')}".strip()
                        for item in order.get("line_items", []):
                            b_rows.append({"Order ID": oid, "Order Date": d_val, "Order Status": status, "Full Name (Billing)": c_name, "Phone (Billing)": bill.get("phone",""), "Item Name": item.get("name"), "Item Cost": item.get("price"), "Quantity": item.get("quantity"), "Order Total Amount": item.get("total")})
                    if len(batch_data) < 100: break
                    page += 1
                return b_rows

            rows = fetch_batch(params)

            # Request 2: Global Open Orders (On-Hold & Pending/Waiting) Regardless of date
            # To catch "hold order time is from any time" and "waiting orders from any time"
            global_params = {
                "per_page": 100,
                "status": "on-hold,pending",
                "orderby": "date",
                "order": "desc"
            }
            global_rows = fetch_batch(global_params)
            
            # Merge and deduplicate by Order ID + Item Name (to avoid double counting if they overlap in the window)
            # Efficiently merging two lists of dicts
            seen_items = set()
            merged_rows = []
            for r in rows + global_rows:
                key = (r["Order ID"], r["Item Name"])
                if key not in seen_items:
                    merged_rows.append(r)
                    seen_items.add(key)
            rows = merged_rows

        else: # Custom Range mode
            start_date = st.session_state.get("wc_sync_start_date", datetime.now().date())
            start_time = st.session_state.get("wc_sync_start_time", (datetime.now() - timedelta(hours=12)).time())
            end_date = st.session_state.get("wc_sync_end_date", datetime.now().date())
            end_time = st.session_state.get("wc_sync_end_time", datetime.now().time())
            params["after"] = f"{start_date}T{start_time.strftime('%H:%M:%S')}"
            params["before"] = f"{end_date}T{end_time.strftime('%H:%M:%S')}"
            params["status"] = "processing,completed,shipped,on-hold,pending"
            
            page = 1
            while True:
                r = requests.get(endpoint, params={**params, "page": page}, auth=HTTPBasicAuth(wc_key, wc_secret), timeout=15)
                r.raise_for_status()
                batch_data = r.json()
                if not batch_data: break
                for order in batch_data:
                    oid, d_val, status = order.get("id"), order.get("date_created"), order.get("status")
                    bill = order.get("billing", {})
                    c_name = f"{bill.get('first_name','')} {bill.get('last_name','')}".strip()
                    for item in order.get("line_items", []):
                        rows.append({"Order ID": oid, "Order Date": d_val, "Order Status": status, "Full Name (Billing)": c_name, "Phone (Billing)": bill.get("phone",""), "Item Name": item.get("name"), "Item Cost": item.get("price"), "Quantity": item.get("quantity"), "Order Total Amount": item.get("total")})
                if len(batch_data) < 100: break
                page += 1

        df_full = pd.DataFrame(rows)
        if df_full.empty:
            return pd.DataFrame(), "woocommerce_api", "N/A"

        # Local partitioning for Operational Cycles
        if sync_mode == "Operational Cycle":
            df_full["dt_parsed"] = pd.to_datetime(df_full["Order Date"], errors="coerce").dt.tz_localize(None)
            curr_start = st.session_state.wc_curr_slot[0].replace(tzinfo=None)
            curr_end = st.session_state.wc_curr_slot[1].replace(tzinfo=None)
            prev_start = st.session_state.wc_prev_slot[0].replace(tzinfo=None)
            prev_end = st.session_state.wc_prev_slot[1].replace(tzinfo=None)
            
            # Define Status Categories
            is_shipped = df_full["Order Status"].isin(["completed", "shipped"])
            is_processing = df_full["Order Status"] == "processing"
            is_hold = df_full["Order Status"] == "on-hold"
            is_waiting = df_full["Order Status"] == "pending"

            # 1. CURRENT SLOT:
            # - processing/shipped order in CURRENT timeframe
            # - hold order from ANY timeframe
            in_curr_win = (df_full["dt_parsed"] >= curr_start) & (df_full["dt_parsed"] < curr_end)
            df_live = df_full[
                (in_curr_win & (is_processing | is_shipped)) |
                (is_hold)
            ].copy()
            st.session_state.wc_curr_df = scrub_raw_dataframe(df_live)
            
            # 2. PREVIOUS SLOT:
            # - shipped from PREVIOUS timeframe
            # - waiting orders (pending) from ANY timeframe
            in_prev_win = (df_full["dt_parsed"] >= prev_start) & (df_full["dt_parsed"] < prev_end)
            df_prev = df_full[
                (in_prev_win & is_shipped) |
                (is_waiting)
            ].copy()
            
            st.session_state.wc_prev_df = scrub_raw_dataframe(df_prev)
        else:
            df_live = df_full
            st.session_state.wc_curr_df = None # Not used

        df_live = scrub_raw_dataframe(df_live)
        
        sync_desc = f"WooCommerce_API_{len(df_live)}_Orders"
        modified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return df_live, sync_desc, modified_at

    except Exception as e:
        log_system_event("WC_API_ERROR", str(e))
        raise RuntimeError(f"Failed to fetch data from WooCommerce: {e}")


def load_live_source():
    """Always use WooCommerce as live source."""
    res = load_from_woocommerce()
    if res:
        st.session_state.live_sync_time = datetime.now()
        return res
    raise ValueError("Failed to load WooCommerce live data.")


def get_items_sold_label(last_updated):
    from datetime import datetime, timedelta, timezone

    tz_bd = timezone(timedelta(hours=6))
    try:
        if (
            isinstance(last_updated, str)
            and last_updated != "N/A"
            and "snapshot" not in last_updated.lower()
        ):
            dt = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
            # Assume last updated time string is already in local tz
            if dt.hour < 16:
                return "Items to be sold"
    except Exception:
        pass

    if datetime.now(tz_bd).hour < 16:
        return "Items to be sold"
    return "Item sold"





def render_dashboard_output(
    drill, summ, top, timeframe, basket, source_name, last_updated="N/A"
):
    """Renders common dashboard widgets/charts/tables/export."""
    # Welcome Insights Popup removed as requested

    # Cross-Slot Comparison Metrics Engine
    if st.session_state.get("wc_sync_mode") == "Operational Cycle" and st.session_state.get("wc_curr_df") is not None and st.session_state.get("wc_prev_df") is not None:
        v_mode = st.session_state.get("wc_view_historical", False)
        c_df, p_df = st.session_state.wc_curr_df, st.session_state.wc_prev_df
        
        # 1. Quantity & Revenue
        c_qty, c_rev = c_df["Quantity"].sum(), (c_df["Quantity"] * c_df["Item Cost"]).sum()
        p_qty, p_rev = p_df["Quantity"].sum(), (p_df["Quantity"] * p_df["Item Cost"]).sum()
        
        # 2. Orders & Basket
        c_ord = c_df["Order ID"].nunique()
        p_ord = p_df["Order ID"].nunique()
        c_bv = (c_rev / c_ord) if c_ord > 0 else 0
        p_bv = (p_rev / p_ord) if p_ord > 0 else 0
        
        # 3. Calculate Deltas (Always Today - Prev)
        d_qty, d_rev = (c_qty - p_qty), (c_rev - p_rev)
        d_ord, d_bv = (c_ord - p_ord), (c_bv - p_bv)
        
        # Select Active Display Values
        main_q = p_qty if v_mode else c_qty
        main_r = p_rev if v_mode else c_rev
        main_o = p_ord if v_mode else c_ord
        main_b = p_bv if v_mode else c_bv
        
        # 4. Contextual Delta Formatting
        prefix = "Today " if v_mode else ""
        suffix = "" if v_mode else " vs Prev"
        
        dq_str = f"{prefix}{d_qty:+,.0f}{suffix}"
        dr_str = f"{prefix}{'+' if d_rev >= 0 else '-'}TK {abs(d_rev):,.0f}{suffix}"
        do_str = f"{prefix}{d_ord:+,.0f}{suffix}"
        db_str = f"{prefix}{'+' if d_bv >= 0 else '-'}TK {abs(d_bv):,.0f}{suffix}"

        with st.container():
            st.markdown('<div id="snapshot-target-main"></div>', unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns([1, 1.3, 1, 1.2, 1.8])
            
            with col1:
                u_label = "Items sold" if v_mode else "Item to be sold"
                st.metric(u_label, f"{main_q:,.0f}", delta=dq_str, delta_color="normal")
            
            with col2:
                st.metric("Revenue", f"TK {main_r:,.0f}", delta=dr_str, delta_color="normal")
            
            with col3:
                st.metric("Orders", f"{main_o:,.0f}", delta=do_str, delta_color="normal")
            
            with col4:
                st.metric("Basket (TK)", f"TK {main_b:,.0f}", delta=db_str, delta_color="normal")
            
            with col5:
                curr_s, curr_e = st.session_state.wc_curr_slot
                prev_s, prev_e = st.session_state.wc_prev_slot
                if not v_mode:
                    st.caption(f"📍 **ACTIVE: Today**")
                    st.caption(f"{curr_s.strftime('%a %d %b, %I%p')} - {curr_e.strftime('%a %d %b, %I%p')}")
                    if st.button(f"⏮️ View Prev ({prev_s.strftime('%d %b')})", use_container_width=True):
                        st.session_state.wc_view_historical = True
                        st.rerun()
                else:
                    st.caption(f"⏮️ **ACTIVE: Previous Window**")
                    st.caption(f"{prev_s.strftime('%a %d %b, %I%p')} → {prev_e.strftime('%a %d %b, %I%p')}")
                    if st.button("📍 Return to Today", use_container_width=True, type="primary"):
                        st.session_state.wc_view_historical = False
                        st.rerun()
            st.divider()

    else:
        # Standard Fallback for non-operational modes
        with st.container():
            st.markdown('<div id="snapshot-target-main"></div>', unsafe_allow_html=True)
            st.subheader("Core Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(get_items_sold_label(last_updated), f"{summ['Total Qty'].sum():,.0f}")
            total_orders = basket.get("total_orders", 0)
            m2.metric("Number of Orders", f"{total_orders:,.0f}" if total_orders else "-")
            m3.metric("Revenue", f"TK {summ['Total Amount'].sum():,.0f}")
            m4.metric("Basket Value (TK)", f"TK {basket.get('avg_basket_value', 0):,.0f}")
            st.divider()

    st.subheader("Performance Outlook")

    sorted_cats = summ.sort_values("Total Amount", ascending=False)[
        "Category"
    ].tolist()
    color_map = {}
    for i, cat in enumerate(sorted_cats):
        val = (
            (i / max(1, len(sorted_cats) - 1)) * 0.85
            if len(sorted_cats) > 1
            else 0.0
        )
        color_map[cat] = px.colors.sample_colorscale("Plasma", [val])[0]

    v1, v2 = st.columns(2)
    with v1:
        fig_pie = px.pie(
            summ,
            values="Total Amount",
            names="Category",
            color="Category",
            hole=0.6,
            title="Revenue Share",
            color_discrete_map=color_map,
        )

        if (
            hasattr(fig_pie, "data")
            and len(fig_pie.data) > 0
            and getattr(fig_pie.data[0], "values", None) is not None
        ):
            t_val = sum(fig_pie.data[0].values)
            t_val = t_val if t_val > 0 else 1
            pos_array = [
                "inside" if (v / t_val) >= 0.02 else "none"
                for v in fig_pie.data[0].values
            ]
        else:
            pos_array = "inside"

        fig_pie.update_layout(
            margin=dict(l=80, r=160, t=40, b=40),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.05,
                font=dict(size=11),
            ),
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        fig_pie.update_traces(
            textposition=pos_array,
            textinfo="label+percent",
            textfont_size=11,
            pull=0.01,
            rotation=270,
            direction="clockwise",
        )
        st.plotly_chart(
            fig_pie,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": False},
        )

    with v2:
        fig_bar = px.bar(
            summ.sort_values("Total Qty", ascending=False),
            x="Category",
            y="Total Qty",
            color="Category",
            title="Volume by Category",
            text_auto=".0f",
            color_discrete_map=color_map,
        )
        fig_bar.update_layout(
            margin=dict(l=12, r=12, t=50, b=12),
            xaxis_title="",
            yaxis_title="Quantity Sold",
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                borderwidth=1,
            ),
        )
        st.plotly_chart(
            fig_bar,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": False},
        )

    render_snapshot_button("snapshot-target-main")
    st.divider()

    st.subheader("Top Products Spotlight")
    spotlight = top.head(10).sort_values("Total Amount", ascending=True)
    fig_top = px.bar(
        spotlight,
        x="Total Amount",
        y="Product Name",
        orientation="h",
        color="Category",
        title="Top 10 products by revenue",
        text_auto=".2s",
    )
    fig_top.update_layout(
        margin=dict(l=12, r=12, t=50, b=12),
        yaxis_title="",
        xaxis_title="Revenue (TK)",
        legend_title="Category",
    )
    st.plotly_chart(
        fig_top,
        use_container_width=True,
        config={"scrollZoom": True, "displayModeBar": False},
    )

    st.subheader("Deep Dive Data")

    tabs = st.tabs(["Summary", "Rankings", "Drilldown"])
    with tabs[0]:
        st.dataframe(
            summ.sort_values("Total Amount", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    with tabs[1]:
        st.dataframe(top.head(20), use_container_width=True, hide_index=True)
    with tabs[2]:
        st.dataframe(
            drill.sort_values(["Category", "Price (TK)"]),
            use_container_width=True,
            hide_index=True,
        )

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as wr:
        summ.to_excel(wr, sheet_name="Summary", index=False)
        top.to_excel(wr, sheet_name="Rankings", index=False)
        drill.to_excel(wr, sheet_name="Details", index=False)

        # Access workbook for premium formatting
        workbook = wr.book
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#D7E4BC", "border": 1})
        currency_fmt = workbook.add_format({"num_format": "#,##0.00"})
        num_fmt = workbook.add_format({"num_format": "#,##0"})

        for sheet_name in wr.sheets:
            ws = wr.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            # Apply consistent column widths
            ws.set_column(0, 5, 20)
            
            if sheet_name == "Summary":
                ws.set_column("B:B", 15, num_fmt)
                ws.set_column("C:C", 18, currency_fmt)
            elif sheet_name == "Details":
                ws.set_column("B:B", 15, currency_fmt)
                ws.set_column("C:C", 15, num_fmt)

    base_name = os.path.splitext(os.path.basename(source_name))[0]
    file_suffix = f"_{timeframe}" if timeframe else ""
    final_filename = f"Report_{base_name}{file_suffix}.xlsx"
    st.download_button("Export Report", data=buf.getvalue(), file_name=final_filename)


def render_manual_tab():
    def _reset_manual_state():
        st.session_state.manual_generate = False
        st.session_state.manual_df = None

    render_reset_confirm("Sales Data Ingestion", "manual", _reset_manual_state)
    
    st.info("💡 Pull precisely filtered historical data from WooCommerce or upload a local file for analysis.")
    src_type = st.radio("Source Type", ["Manual File Upload", "WooCommerce Custom Pull"], horizontal=True, key="ingestion_src_type")
    
    df = None
    source_name = ""
    
    if src_type == "Manual File Upload":
        uploaded_file = st.file_uploader("Upload Product Sales File", type=["xlsx", "csv"], key="manual_uploader")
        if uploaded_file:
            df = read_sales_file(uploaded_file, uploaded_file.name)
            source_name = uploaded_file.name
    else:
        # WooCommerce Custom Pull Logic (Moved from Live Tab)
        with st.expander("🔍 Filtered Data Acquisition", expanded=True):
            st.caption("Specify the exact time window for the data you wish to ingest.")
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start Date", value=datetime.now().date(), key="ingest_start_d")
            start_time = c1.time_input("Start Time", value=(datetime.now() - timedelta(hours=24)).time(), key="ingest_start_t")
            end_date = c2.date_input("End Date", value=datetime.now().date(), key="ingest_end_d")
            end_time = c2.time_input("End Time", value=datetime.now().time(), key="ingest_end_t")
            
            if st.button("📩 Fetch & Review Data", use_container_width=True, type="primary"):
                # Temporarily set session state for the fetcher
                st.session_state["wc_sync_mode"] = "Custom Range"
                st.session_state["wc_sync_start_date"] = start_date
                st.session_state["wc_sync_start_time"] = start_time
                st.session_state["wc_sync_end_date"] = end_date
                st.session_state["wc_sync_end_time"] = end_time
                
                try:
                    with st.spinner("Connecting to WooCommerce API..."):
                        # We use load_from_woocommerce directly to get full control
                        df_res, src_res, _ = load_from_woocommerce()
                        if not df_res.empty:
                            st.session_state.manual_df = df_res
                            st.session_state.manual_source_name = src_res
                            st.success(f"Successfully ingested {len(df_res)} records.")
                        else:
                            st.warning("No data found for the selected time range.")
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
        
        if st.session_state.get("manual_df") is not None:
            df = st.session_state.manual_df
            source_name = st.session_state.get("manual_source_name", "WooCommerce_Custom_Pull")

    if df is None:
        return

    try:
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

        final_mapping = {
            "name": mapped_name,
            "cost": mapped_cost,
            "qty": mapped_qty,
            "date": mapped_date if mapped_date != "None" else None,
            "order_id": mapped_order if mapped_order != "None" else None,
            "phone": mapped_phone if mapped_phone != "None" else None,
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
            drill, summ, top, timeframe, basket = process_data(df, final_mapping)
            if drill is not None:
                manual_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                render_dashboard_output(
                    drill,
                    summ,
                    top,
                    timeframe,
                    basket,
                    uploaded_file.name,
                    manual_updated,
                )

    except Exception as e:
        log_system_event("FILE_ERROR", str(e))
        st.error(f"File error: {e}")


def render_live_tab():
    def _reset_live_state():
        st.session_state.wc_curr_df = None
        st.session_state.wc_prev_df = None
        st.session_state.live_sync_time = None
        st.session_state.wc_view_historical = False
        st.session_state.wc_sync_mode = "Operational Cycle"

    render_reset_confirm("Live Dashboard", "live", _reset_live_state)
    """Always running dashboard from selected source."""
    tz_bd = timezone(timedelta(hours=6))
    current_t = datetime.now(tz_bd).strftime("%B %d, %Y %I:%M %p")
    logo_src = "https://logo.clearbit.com/deencommerce.com"
    try:
        logo_jpg = os.path.join("assets", "deen_logo.jpg")
        if os.path.exists(logo_jpg):
            with open(logo_jpg, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            logo_src = f"data:image/png;base64,{b64}"
    except Exception:
        pass

    # Use global imports
    tz_bd = timezone(timedelta(hours=6))

    st.markdown(
        f"""
        <div>
            <div id="dynamic-clock-live" style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">Current time: {datetime.now(tz_bd).strftime('%B %d, %Y %I:%M %p')}</div>
            <script>
                (function() {{
                    function update() {{
                        const options = {{ month: 'long', day: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }};
                        const now = new Date();
                        const timeStr = now.toLocaleString('en-US', options);
                        const el = document.getElementById('dynamic-clock-live');
                        if (el) el.innerHTML = "Current time: " + timeStr;
                    }}
                    setInterval(update, 1000);
                    update();
                }})();
            </script>
        </div>
        """,
        unsafe_allow_html=True,
    )
    welcome_html = f"""
    <div class="hub-welcome-banner">
        <div style="font-weight: 700; font-size: 1.15rem; margin-bottom: 4px;">Welcome! Today's Actionable Insights</div>
        <div style="font-size: 0.85rem; opacity: 0.9;">
            Powered by <a href="https://deencommerce.com/" target="_blank" style="text-decoration:none;">
                <img src="{logo_src}" width="16" style="vertical-align:middle; margin: 0 3px; border-radius:2px;" onerror="this.style.display='none'">
                <b>DEEN commerce</b>
            </a>
        </div>
    </div>
    """
    st.markdown(welcome_html, unsafe_allow_html=True)
    
    # Force Operational Cycle in live dashboard
    st.session_state["wc_sync_mode"] = "Operational Cycle"

    # Freshness & Direct Action Row
    c_f1, c_f2 = st.columns([6, 1])
    with c_f1:
        if st.session_state.get("live_sync_time"):
            diff = datetime.now() - st.session_state.live_sync_time
            mins = int(diff.total_seconds() / 60)
            sync_label = "Just now" if mins < 1 else f"{mins}m ago"
            st.caption(f"🔄 Last Synced: {sync_label}")
    with c_f2:
        if st.button("🔄 Sync", help="Force Operational Re-sync", use_container_width=True):
            st.rerun()

    if hasattr(st, "autorefresh"):
        st.autorefresh(interval=30000, key="live_autorefresh")

    try:
        df_live, source_name, modified_at = load_live_source()

        # Handle 'Time Travel' view mode
        if st.session_state.get("wc_view_historical") and "wc_prev_df" in st.session_state:
            prev_df = st.session_state.wc_prev_df
            if prev_df is not None and not prev_df.empty:
                df_live = prev_df
                prev_s, prev_e = st.session_state.wc_prev_slot
                source_name = f"PREV_SLOT_{prev_s.strftime('%a_%d%b')}"
                modified_at = "HISTORICAL_SNAPSHOT"
            else:
                st.warning("No data found for the previous slot. Reverting to current.")
                st.session_state.wc_view_historical = False

        auto_cols = find_columns(df_live)
        missing_required = [k for k in ["name", "cost", "qty"] if k not in auto_cols]
        if missing_required:
            st.error(f"Cannot auto-map required columns: {', '.join(missing_required)}")
            st.dataframe(df_live.head(20), use_container_width=True)
            return

        live_mapping = {
            "name": auto_cols.get("name"),
            "cost": auto_cols.get("cost"),
            "qty": auto_cols.get("qty"),
            "date": auto_cols.get("date"),
            "order_id": auto_cols.get("order_id"),
            "phone": auto_cols.get("phone"),
        }

        drill, summ, top, timeframe, basket = process_data(df_live, live_mapping)
        if drill is not None:
            render_dashboard_output(
                drill, summ, top, timeframe, basket, source_name, modified_at
            )

    except Exception as e:
        log_system_event("LIVE_FILE_ERROR", str(e))
        st.error(f"Live source error: {e}")


def fetch_woocommerce_stock():
    """Fetches real-time stock levels and maps categories from sum_quantities logic."""
    wc_info = st.secrets.get("woocommerce", {})
    wc_url = wc_info.get("store_url") or os.environ.get("WC_URL")
    wc_key = wc_info.get("consumer_key") or os.environ.get("WC_KEY")
    wc_secret = wc_info.get("consumer_secret") or os.environ.get("WC_SECRET")

    if not wc_url or not wc_key or not wc_secret:
        st.error("WooCommerce credentials missing.")
        return None

    # Logic ported from sum_quantities.py
    cat_rules = {
        "Jeans Slim Fit": lambda n: "jeans" in n and "slim fit" in n,
        "Jeans Regular Fit": lambda n: "jeans" in n and "regular fit" in n,
        "Jeans Straight Fit": lambda n: "jeans" in n and "straight fit" in n,
        "Panjabi": lambda n: "panjabi" in n,
        "T-shirt Basic Full": lambda n: "t-shirt" in n and "full sleeve" in n,
        "T-shirt Drop-Shoulder": lambda n: "t-shirt" in n and ("drop-shoulder" in n or "drop shoulder" in n),
        "T-shirt Basic Half": lambda n: "t-shirt" in n and not ("full sleeve" in n or "drop-shoulder" in n or "drop shoulder" in n),
        "Sweatshirt": lambda n: "sweatshirt" in n,
        "Turtle-Neck": lambda n: "turtle-neck" in n or "turtleneck" in n,
        "Tank-Top": lambda n: "tank-top" in n or "tank top" in n,
        "Trousers Terry Fabric": lambda n: (("trouser" in n or "jogger" in n or "pant" in n) and "terry" in n),
        "Trousers Cotton Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n) and ("twill" in n or "chino" in n or "cotton" in n),
        "Polo": lambda n: "polo" in n,
        "Kaftan Shirt": lambda n: "kaftan" in n,
        "Contrast Stich": lambda n: "contrast stitch" in n or "contrast stich" in n,
        "Denim Shirt": lambda n: "denim" in n and "shirt" in n,
        "Flannel Shirt": lambda n: "flannel" in n and "shirt" in n,
        "Casual Shirt Full": lambda n: "shirt" in n and "full sleeve" in n and not any(k in n for k in ["denim", "flannel", "kaftan", "contrast", "stitch", "stich", "polo", "sweatshirt"]),
        "Casual Shirt Half": lambda n: "shirt" in n and not any(k in n for k in ["full sleeve", "denim", "flannel", "kaftan", "contrast", "stitch", "stich", "polo", "t-shirt", "sweatshirt"]),
        "Belt": lambda n: "belt" in n,
        "Wallet Bifold": lambda n: "wallet" in n and "bifold" in n,
        "Wallet Trifold": lambda n: "wallet" in n and "trifold" in n,
        "Wallet Long": lambda n: "wallet" in n and "long" in n,
        "Passport Holder": lambda n: "passport holder" in n,
        "Mask": lambda n: "mask" in n,
        "Card Holder": lambda n: "card holder" in n,
        "Water Bottle": lambda n: "water bottle" in n,
        "Boxer": lambda n: "boxer" in n,
    }

    def map_category(name):
        n = name.lower()
        for cat, func in cat_rules.items():
            if func(n): return cat
        return "Uncategorized"

    endpoint = f"{wc_url.rstrip('/')}/wp-json/wc/v3/products"
    stock_data = []
    
    try:
        page = 1
        with st.spinner("📦 Fetching live inventory and mapping categories..."):
            while True:
                r = requests.get(
                    endpoint,
                    params={"per_page": 100, "page": page},
                    auth=HTTPBasicAuth(wc_key, wc_secret),
                    timeout=25
                )
                r.raise_for_status()
                products = r.json()
                if not products: break
                
                for p in products:
                    p_id, p_name = p.get("id"), p.get("name")
                    p_type = p.get("type", "simple")
                    
                    if p_type == "variable":
                        v_r = requests.get(f"{endpoint}/{p_id}/variations", params={"per_page": 100}, auth=HTTPBasicAuth(wc_key, wc_secret), timeout=15)
                        if v_r.status_code == 200:
                            for v in v_r.json():
                                full_name = f"{p_name} - {v.get('attributes',[{}])[0].get('option','N/A')}"
                                stock_data.append({
                                    "Category": map_category(p_name), # Map by base product name for broad categorization
                                    "Product": full_name,
                                    "SKU": v.get("sku") or f"P{p_id}-V{v.get('id')}",
                                    "Stock": v.get("stock_quantity") if v.get("manage_stock") else 0,
                                    "Price": v.get("price", "0"),
                                    "Status": v.get("stock_status", "unknown").title()
                                })
                    else:
                        stock_data.append({
                            "Category": map_category(p_name),
                            "Product": p_name,
                            "SKU": p.get("sku") or f"P{p_id}",
                            "Stock": p.get("stock_quantity") if p.get("manage_stock") else 0,
                            "Price": p.get("price", "0"),
                            "Status": p.get("stock_status", "unknown").title()
                        })
                if len(products) < 100: break
                page += 1
                
        df = pd.DataFrame(stock_data)
        if not df.empty:
            df["Stock"] = pd.to_numeric(df["Stock"], errors="coerce").fillna(0).astype(int)
            df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
            # Default filter: Only show in-stock
            df = df[df["Stock"] > 0]
        return df

    except Exception as e:
        log_system_event("STOCK_SYNC_ERROR", str(e))
        st.error(f"Stock fetch failed: {e}")
        return None


def render_stock_analytics_tab():
    """Renders the category-wise stock monitoring interface."""
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📦 Current Stock Intelligence")
    
    col_sync, col_info = st.columns([1, 4])
    with col_sync:
        if st.button("🔄 Force Re-Sync", use_container_width=True, type="primary"):
            st.session_state.wc_stock_df = fetch_woocommerce_stock()
            st.session_state.stock_sync_time = datetime.now()
            st.rerun()

    # Automatically trigger fetch on first load if missing
    if "wc_stock_df" not in st.session_state or st.session_state.wc_stock_df is None:
        st.session_state.wc_stock_df = fetch_woocommerce_stock()
        st.session_state.stock_sync_time = datetime.now()
        if st.session_state.wc_stock_df is not None:
            st.rerun()

    if "wc_stock_df" not in st.session_state or st.session_state.wc_stock_df is None:
        st.info("Directly pull real-time inventory levels by Shift-Category rules.")
        return

    df = st.session_state.wc_stock_df
    if df is None or df.empty:
        st.warning("No in-stock items found.")
        return

    # Stock Summary by Shift-Category
    st.divider()
    
    total_qty = df["Stock"].sum()
    low_stock = df[df["Stock"] < 10].shape[0]
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Items in Stock", f"{total_qty:,.0f}")
    k2.metric("Low Stock Alerts", low_stock, delta="Action Needed" if low_stock > 0 else None, delta_color="inverse")
    k3.metric("Mapped Categories", df["Category"][df["Category"] != "Uncategorized"].nunique())

    # Category Volume Table
    st.subheader("Inventory by Product Category")
    cat_summ = df.groupby("Category")["Stock"].sum().reset_index()
    cat_summ = cat_summ.sort_values("Stock", ascending=False)
    
    v1, v2 = st.columns([2, 3])
    with v1:
        st.dataframe(cat_summ, use_container_width=True, hide_index=True, column_config={"Stock": st.column_config.NumberColumn(format="%d")})
    with v2:
        fig = px.bar(cat_summ.head(15), x="Stock", y="Category", orientation="h", title="Top 15 Categories by Volume", color="Stock", color_continuous_scale="Viridis")
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Search & Filter
    st.divider()
    st.subheader("Granular Stock Details")
    search = st.text_input("🔍 Filter by Product Name, SKU, or Category", "").strip().lower()
    
    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[
            filtered_df["Product"].str.lower().str.contains(search) | 
            filtered_df["SKU"].str.lower().str.contains(search) |
            filtered_df["Category"].str.lower().str.contains(search)
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Stock": st.column_config.NumberColumn(format="%d"),
            "Price": st.column_config.NumberColumn(format="TK %.0f")
        }
    )
    
    st.caption(f"Database last refreshed: {st.session_state.get('stock_sync_time', datetime.now()).strftime('%I:%M %p')}")
    st.markdown('</div>', unsafe_allow_html=True)

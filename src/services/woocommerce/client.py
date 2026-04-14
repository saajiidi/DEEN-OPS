import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from requests.auth import HTTPBasicAuth

from src.config.settings import get_setting
from src.processing.column_detection import scrub_raw_dataframe
from src.utils.logging import log_system_event


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
        tz_bd = timezone(timedelta(hours=6))

        # Determine pulling window based on user selection in session state
        sync_mode = st.session_state.get("wc_sync_mode", "Operational Cycle")

        params = {
            "per_page": 100,
            "status": "processing,completed,shipped,confirmed",
            "orderby": "date",
            "order": "desc"
        }

        def get_operational_sync_window(ref_time):
            # Thursday 5:30 PM to Saturday 5:30 PM is the weekend slot (Bangladesh)
            anchor_5_30pm = ref_time.replace(hour=17, minute=30, second=0, microsecond=0)

            # RULE: Active shift starts yesterday 5:30 PM and stays active until MIDNIGHT TONIGHT
            start = anchor_5_30pm - timedelta(days=1)

            # Weekend adjustment: Friday is covered by the Thu-Sat slot
            if start.weekday() == 4: # Friday
                start -= timedelta(days=1) # Back to Thu 17:30

            # The window for fetch needs to be broad enough to capture the entire active shift
            # We set end to TONIGHT 23:59:59 to capture evening orders
            end = ref_time.replace(hour=23, minute=59, second=59, microsecond=0)
            return start, end

        # Specialized Fetching Strategy for Operational Cycle
        if sync_mode == "Operational Cycle":
            now_bd = datetime.now(tz_bd)
            curr_start, curr_end = get_operational_sync_window(now_bd)
            prev_start, prev_end = get_operational_sync_window(curr_start - timedelta(seconds=1))

            # Request 1: All relevant statuses within the broad operational window
            # (since prev_start, to catch both current and previous slots)
            # Request: Broad operational pool (From Previous Slot start until NOW)
            # This ensures both yesterday's snapshot and today's active window stay populated.
            params["after"] = prev_start.isoformat()
            params["before"] = now_bd.replace(hour=23, minute=59, second=59).isoformat()
            params["status"] = "processing,completed,shipped,on-hold,pending,confirmed"

        def fetch_batch(p):
            # Optimize payload size by requesting only necessary fields
            fields = "id,date_created,status,billing,shipping,payment_method_title,line_items,total"
            p["_fields"] = fields
            
            b_rows = []
            
            # First request to get total pages
            try:
                r = requests.get(endpoint, params={**p, "page": 1}, auth=HTTPBasicAuth(wc_key, wc_secret), timeout=15)
                r.raise_for_status()
                total_pages = int(r.headers.get('X-WP-TotalPages', 1))
                batch_data = r.json()
                
                def process_batch(data):
                    processed = []
                    for order in data:
                        oid, d_val, status = order.get("id"), order.get("date_created"), order.get("status")
                        bill = order.get("billing", {})
                        ship = order.get("shipping", {})
                        c_name = f"{bill.get('first_name','')} {bill.get('last_name','')}".strip()
                        pmt = order.get("payment_method_title", "")
                        for item in order.get("line_items", []):
                            processed.append({
                                "Order ID": oid,
                                "Order ID": oid,
                                "Order Date": d_val,
                                "Order Status": status,
                                "Full Name (Billing)": c_name,
                                "Phone (Billing)": bill.get("phone",""),
                                "Shipping Address 1": ship.get("address_1", ""),
                                "Shipping City": ship.get("city", ""),
                                "State Name (Billing)": bill.get("state", ""),
                                "Item Name": item.get("name"),
                                "SKU": item.get("sku", ""),
                                "Item Cost": item.get("price"),
                                "Quantity": item.get("quantity"),
                                "Order Total Amount": order.get("total"),
                                "Payment Method Title": pmt
                            })
                    return processed

                b_rows.extend(process_batch(batch_data))
                
                if total_pages > 1:
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=min(total_pages, 8)) as executor:
                        pages_to_fetch = range(2, total_pages + 1)
                        futures = []
                        for pg in pages_to_fetch:
                            futures.append(executor.submit(
                                lambda pge=pg: requests.get(endpoint, params={**p, "page": pge}, auth=HTTPBasicAuth(wc_key, wc_secret), timeout=15).json()
                            ))
                        for future in futures:
                            b_rows.extend(process_batch(future.result()))
            except Exception as e:
                log_system_event("WC_FETCH_BATCH_ERROR", str(e))
                # Fallback to empty list if critical error
                if not b_rows: return []
            
            return b_rows

        # Specialized Fetching Strategy for Operational Cycle
        if sync_mode == "Operational Cycle":
            now_bd = datetime.now(tz_bd)
            curr_start, curr_end = get_operational_sync_window(now_bd)
            prev_start, prev_end = get_operational_sync_window(curr_start - timedelta(seconds=1))

            params["after"] = prev_start.isoformat()
            params["before"] = now_bd.replace(hour=23, minute=59, second=59).isoformat()
            params["status"] = "processing,completed,shipped,on-hold,pending,confirmed"

            rows = fetch_batch(params)

            # Request 2: Global Open Orders
            global_params = {
                "per_page": 100,
                "status": "on-hold,pending,confirmed",
                "orderby": "date",
                "order": "desc"
            }
            global_rows = fetch_batch(global_params)

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
            params["status"] = "processing,completed,shipped,on-hold,pending,confirmed"

            rows = fetch_batch(params)

        df_full = pd.DataFrame(rows)
        if df_full.empty:
            return {
                "df_to_return": pd.DataFrame(),
                "sync_desc": "woocommerce_api_empty",
                "modified_at": "N/A",
                "partitions": {},
                "slots": {}
            }

        # Local partitioning for Operational Cycles (v9.8 Refined Rules)
        if sync_mode == "Operational Cycle":
            df_full["dt_parsed"] = pd.to_datetime(df_full["Order Date"], errors="coerce").dt.tz_localize(None)

            now_bd = datetime.now(tz_bd)
            ref_now = now_bd.replace(tzinfo=None)

            # THE ANCHOR: Today's 17:30 Cutoff
            cutoff_today = ref_now.replace(hour=17, minute=30, second=0, microsecond=0)

            # THE START OF THE CURRENT ACTIVE SLOT (Last Day 17:30)
            prev_cutoff = cutoff_today - timedelta(days=1)

            # WEEKEND RULE: On Saturday, the active shift started Thursday 17:30
            if now_bd.weekday() == 5: # Saturday
                prev_cutoff = cutoff_today - timedelta(days=2) # Thu 17:30 -> Sat 17:30

            # THE PREVIOUS HISTORICAL SLOT (Used for "Prev" tab and deltas)
            day_before_prev = prev_cutoff - timedelta(days=1)

            # SUNDAY EXCEPTION: Previous Day Sales is Thursday 5:30 PM to Saturday 5:30 PM
            if now_bd.weekday() == 6: # Sunday
                prev_cutoff = cutoff_today - timedelta(days=1) # Sat 17:30
                day_before_prev = prev_cutoff - timedelta(days=2) # Thu 17:30

            # Define Status Categories
            is_confirmed = df_full["Order Status"] == "confirmed"
            is_shipped = df_full["Order Status"].isin(["completed", "shipped"])
            is_processing = df_full["Order Status"] == "processing"
            is_hold = df_full["Order Status"] == "on-hold"
            is_waiting = df_full["Order Status"] == "pending"

            # REFINED CUTOFFS
            shipped_limit = cutoff_today + timedelta(minutes=30)
            proc_limit = cutoff_today + timedelta(minutes=15)

            # SNAPSHOT 1: TODAY (Active Shift - Now includes intake)
            # v11.6: Confirmed orders are included regardless of date
            df_live = df_full[
                ( (df_full["dt_parsed"] >= prev_cutoff) & (df_full["dt_parsed"] <= shipped_limit) & (is_shipped | is_waiting) ) |
                ( is_processing & (df_full["dt_parsed"] <= proc_limit) ) |
                is_confirmed
            ].copy()

            # SNAPSHOT 2: YESTERDAY (Historical Performance)
            df_prev = df_full[
                (df_full["dt_parsed"] >= day_before_prev) &
                (df_full["dt_parsed"] < prev_cutoff) &
                is_shipped
            ].copy()

            # SNAPSHOT 3: BACKLOG (Hold + Waiting + Late Ops)
            df_backlog = df_full[
                is_hold | is_waiting |
                (is_processing & (df_full["dt_parsed"] > proc_limit))
            ].copy()

            # v9.8 Selective Slot Return
            current_hour = now_bd.hour
            if 0 <= current_hour < 6:
                df_to_return = df_backlog
                slot_label = "Backlog"
            else:
                df_to_return = df_live
                slot_label = "Today"
        else:
            df_to_return = df_full
            slot_label = "Custom"
            df_live, df_prev, df_backlog = None, None, None
            prev_cutoff, cutoff_today, day_before_prev = None, None, None

        df_to_return = scrub_raw_dataframe(df_to_return)

        # Package results for caller to handle session state (v9.8 Stateless Cache)
        results = {
            "df_to_return": df_to_return,
            "sync_desc": f"WooCommerce_{slot_label}_API_{len(df_to_return)}_Orders",
            "modified_at": datetime.now(tz_bd).strftime("%Y-%m-%d %H:%M:%S"),
            "partitions": {
                "wc_curr_df": scrub_raw_dataframe(df_live) if df_live is not None else None,
                "wc_prev_df": scrub_raw_dataframe(df_prev) if df_prev is not None else None,
                "wc_backlog_df": scrub_raw_dataframe(df_backlog) if df_backlog is not None else None,
            },
            "slots": {
                "wc_curr_slot": (prev_cutoff, cutoff_today) if prev_cutoff else None,
                "wc_prev_slot": (day_before_prev, prev_cutoff) if day_before_prev else None,
                "wc_backlog_slot": (cutoff_today, cutoff_today + timedelta(days=1)) if cutoff_today else None,
            }
        }
        return results

    except Exception as e:
        log_system_event("WC_API_ERROR", str(e))
        raise RuntimeError(f"Failed to fetch data from WooCommerce: {e}")


def load_live_source():
    """Stateless fetch with stateful session update."""
    results = load_from_woocommerce()
    if results and isinstance(results, dict):
        # 1. Update Partitioned State
        partitions = results.get("partitions", {})
        for key, df in partitions.items():
            if df is not None:
                st.session_state[key] = df

        # 2. Update Slot Metadata
        slots = results.get("slots", {})
        for key, val in slots.items():
            if val is not None:
                st.session_state[key] = val

        # 3. Update Sync Metadata
        st.session_state.live_sync_time = datetime.now()

        # 4. Return tuple for legacy unpacking
        return results["df_to_return"], results["sync_desc"], results["modified_at"]

    # Handle legacy return if any (for safety)
    if results:
        st.session_state.live_sync_time = datetime.now()
        return results

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

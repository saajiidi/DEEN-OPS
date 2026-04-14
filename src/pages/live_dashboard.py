import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.components.widgets import render_reset_confirm
from src.processing.column_detection import find_columns
from src.processing.data_processing import prepare_granular_data, aggregate_data
from src.pages.dashboard_output import render_dashboard_output
from src.services.woocommerce.client import load_live_source
from src.utils.logging import log_system_event


def render_live_tab():
    def _reset_live_state():
        st.session_state.wc_curr_df = None
        st.session_state.wc_prev_df = None
        st.session_state.live_sync_time = None
        st.session_state.wc_view_historical = False
        st.session_state.wc_sync_mode = "Operational Cycle"

    render_reset_confirm("Live Dashboard", "live", _reset_live_state)
    st.session_state.manual_tab_active = False # v11.3 Flag Reset
    """Always running dashboard from selected source."""
    tz_bd = timezone(timedelta(hours=6))
    current_t = datetime.now(tz_bd).strftime("%B %d, %Y %I:%M %p")
    # logo_src logically moved to render_dashboard_output

    # Use global imports
    tz_bd = timezone(timedelta(hours=6))

    # Force Operational Cycle in live dashboard
    st.session_state["wc_sync_mode"] = "Operational Cycle"

    # Standardize autorefresh for Live Dashboard

    try:
        df_live, source_name, modified_at = load_live_source()

        # Handle v9.5 Multi-Mode Shift Navigation
        nav_mode = st.session_state.get("wc_nav_mode", "Today")
        if nav_mode == "Prev" and "wc_prev_df" in st.session_state:
            df_live = st.session_state.wc_prev_df
            p_s, p_e = st.session_state.get("wc_prev_slot", (datetime.now(), datetime.now()))
            source_name = f"PREV_SLOT_{p_s.strftime('%a_%d%b')}"
            modified_at = "HISTORICAL_SNAPSHOT"
        elif nav_mode == "Backlog" and "wc_backlog_df" in st.session_state:
            df_live = st.session_state.wc_backlog_df
            b_s, b_e = st.session_state.get("wc_backlog_slot", (datetime.now(), datetime.now()))
            source_name = f"INCOMING_BATCH_{b_s.strftime('%H:%M')}"
            modified_at = "BACKLOG_QUEUE"
        elif nav_mode == "Today" and "wc_curr_df" in st.session_state:
            df_live = st.session_state.wc_curr_df
            # default df_live from load_live_source is already the current one

        if df_live is None or df_live.empty:
            st.warning(f"No data found for the {nav_mode} slot.")
            # Fallback to Today if we were in another mode
            if nav_mode != "Today":
                st.session_state.wc_nav_mode = "Today"
                st.rerun()

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

        df_standard, timeframe = prepare_granular_data(df_live, live_mapping)
        if not df_standard.empty:
            drill, summ, top, basket = aggregate_data(df_standard, live_mapping)
            render_dashboard_output(
                drill,
                summ,
                top,
                timeframe,
                basket,
                source_name,
                modified_at,
                granular_df=df_standard
            )


    except Exception as e:
        log_system_event("LIVE_FILE_ERROR", str(e))
        st.error(f"Live source error: {e}")
        st.info("\U0001f4a1 Tip: If WooCommerce is down, use the '\U0001f4e5 Sales Data Ingestion' tab to pull fallback data from Google Sheets.")

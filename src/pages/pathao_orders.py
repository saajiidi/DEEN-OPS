import pandas as pd
import streamlit as st
import os
import json

from src.utils.logging import log_error
from src.state.persistence import clear_state_keys, save_state
from src.processing.order_processor import process_orders_dataframe
from src.components.widgets import (
    render_action_bar,
    render_file_summary,
    render_reset_confirm,
    section_card,
)
from src.utils.file_io import to_excel_bytes, read_uploaded
from src.components.status import render_status_toggle
from src.services.pathao.client import PathaoClient
from src.config.ui_config import PATHAO_CONFIG, DEFAULT_GSHEET_URL

REQUIRED_COLUMNS = ["Phone (Billing)"]


def _reset_pathao_state():
    clear_state_keys(["pathao_res_df", "pathao_preview_df", "pathao_uploaded_name"])


def render_pathao_tab():
    render_reset_confirm("Pathao Processor", "pathao", _reset_pathao_state)

    # Pathao API Sync Section
    with st.expander("⚙️ Pathao API & Sync Settings", expanded=False):
        st.markdown("### Location Database Sync")

        pathao_map_path = "resources/pathao_map.json"
        if os.path.exists(pathao_map_path):
            from datetime import datetime
            mtime = os.path.getmtime(pathao_map_path)
            updated_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            render_status_toggle("Local DB Loaded", "success", f"Last updated: {updated_str}")
        else:
            render_status_toggle("No Local Data", "warning", "Sync required for smart zone matching.")

        st.info("Sync your local database with Pathao's official city, zone, and area list for more accurate mapping.")

        if st.button("🔄 Sync Available Locations from Pathao", use_container_width=True):
            with st.status("Connecting to Pathao API...", expanded=True) as status:
                try:
                    client = PathaoClient(**PATHAO_CONFIG)
                    st.write("Fetching cities...")
                    cities, error = client.get_cities()

                    if error:
                        st.error(f"Sync Failed: {error}")
                        status.update(label="Sync Failed", state="error")
                    elif not cities:
                        st.warning("Connected successfully, but Pathao returned an empty city list. (This is common in restricted Sandbox accounts)")
                        status.update(label="Sync Complete (Empty)", state="complete")
                    else:
                        full_map = {}
                        progress_bar = st.progress(0)
                        for i, city in enumerate(cities):
                            c_id = city['city_id']
                            c_name = city['city_name']
                            st.write(f"Syncing {c_name}...")
                            zones, z_err = client.get_zones(c_id)

                            full_map[c_name] = {"city_id": c_id, "zones": {}}
                            if not z_err:
                                for zone in zones:
                                    z_id = zone['zone_id']
                                    z_name = zone['zone_name']
                                    areas, a_err = client.get_areas(z_id)
                                    full_map[c_name]["zones"][z_name] = {"zone_id": z_id, "areas": areas if not a_err else []}

                            progress_bar.progress((i + 1) / len(cities))

                        os.makedirs("resources", exist_ok=True)
                        with open("resources/pathao_map.json", "w") as f:
                            json.dump(full_map, f, indent=4)

                        st.success(f"Successfully synced {len(cities)} cities and their areas!")
                        status.update(label="Sync Complete", state="complete")
                except Exception as e:
                    st.error(f"Sync failed: {e}")
                    status.update(label="Sync Error", state="error")

    up_pathao = st.file_uploader("", type=["xlsx", "csv"], key="pathao_up")

    st.markdown('<div style="margin-top: -12px;"></div>', unsafe_allow_html=True)
    c_live, c_gsheet = st.columns(2)
    with c_live:
        fetch_live_clicked = st.button(
            "🔗 Pull from Live Dash",
            type="secondary",
            use_container_width=True,
            key="pathao_live",
        )
    with c_gsheet:
        if st.button("📩 Fetch from GSheet", use_container_width=True, type="secondary", key="pathao_gsheet"):
            try:
                with st.spinner("Fetching from Google Sheet..."):
                    df_res = pd.read_csv(DEFAULT_GSHEET_URL)
                    st.session_state.pathao_preview_df = df_res
                    st.session_state.pathao_uploaded_name = "Google_Sheet_Export"
                    st.session_state.pathao_auto_process = True
                    st.rerun()
            except Exception as e:
                st.error(f"GSheet failed: {e}")

    preview_df = None
    valid_file = False

    if fetch_live_clicked:
        try:
            # v9.8 Rapid In-Memory Pull
            if st.session_state.get("wc_curr_df") is not None:
                df_live = st.session_state.wc_curr_df
                source_name = "Dashboard_Live_Today"
                st.info("⚡ Instant Pull: Using Today's Active Shift data from Dashboard.")
            else:
                from src.services.woocommerce.client import load_live_source
                with st.spinner("Connecting to WooCommerce API..."):
                    df_live, source_name, _ = load_live_source()

            preview_df = df_live
            st.session_state.pathao_preview_df = preview_df
            st.session_state.pathao_uploaded_name = source_name
            st.session_state.pathao_auto_process = True

            missing = [c for c in REQUIRED_COLUMNS if c not in preview_df.columns]
            valid_file = len(missing) == 0
            st.success(f"Successfully pulled {len(df_live)} records.")

        except Exception as exc:
            log_error(exc, context="Pathao WooCommerce Pull")
            st.error(f"Failed to fetch data: {exc}")
    elif up_pathao:
        try:
            preview_df = read_uploaded(up_pathao)
            st.session_state.pathao_preview_df = preview_df
            st.session_state.pathao_uploaded_name = up_pathao.name
            valid_file = render_file_summary(up_pathao, preview_df, REQUIRED_COLUMNS)
        except Exception as exc:
            log_error(exc, context="Pathao Upload")
            st.error("Failed to read uploaded file.")
    elif st.session_state.get("pathao_preview_df") is not None:
        preview_df = st.session_state.pathao_preview_df
        missing = [c for c in REQUIRED_COLUMNS if c not in preview_df.columns]
        valid_file = len(missing) == 0

    run_clicked, clear_clicked = render_action_bar(
        primary_label="Process orders",
        primary_key="pathao_process_btn",
        secondary_label="Clear upload",
        secondary_key="pathao_clear_btn",
    )

    if st.session_state.get("pathao_auto_process"):
        run_clicked = True
        st.session_state.pathao_auto_process = False

    if clear_clicked:
        _reset_pathao_state()
        st.rerun()

    if run_clicked:
        if preview_df is None or not valid_file:
            st.warning(
                "Upload a valid file or pull from live source before processing."
            )
        else:
            try:
                with st.status("Processing orders...", expanded=True) as status:
                    st.write("Applying standard cleanup and address formatting...")
                    result_df = process_orders_dataframe(preview_df)
                    st.session_state.pathao_res_df = result_df
                    save_state()
                    status.update(
                        label="Processing complete", state="complete", expanded=False
                    )
                st.success(f"Processed {len(result_df)} grouped orders.")
            except Exception as exc:
                log_error(exc, context="Pathao Processor")
                st.error("Pathao processing failed. Check System Logs for details.")

    result_df = st.session_state.get("pathao_res_df")
    if result_df is not None:
        with st.expander("Preview output", expanded=True):
            st.dataframe(result_df, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download repaired file",
                to_excel_bytes(result_df, sheet_name="Pathao"),
                "Pathao_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

        with c2:
            if st.button(
                "Generate Verification Links",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.show_vlink_gen = True

        if st.session_state.get("show_vlink_gen"):
            with st.status("Generating links...", expanded=True):
                import random

                df_v = result_df.copy()
                domain = "https://deencommerce.com/v"
                # Use Phone or Order ID
                links = []
                for _, row in df_v.iterrows():
                    token = f"{random.getrandbits(32):08x}"
                    order_id = str(row.get("Order ID", "VERIFY"))
                    links.append(f"{domain}/verify?id={order_id}&token={token}")
                df_v["Verification Link"] = links
                st.session_state.pathao_vlink_df = df_v
                st.success("Verification links generated!")

            vlink_df = st.session_state.get("pathao_vlink_df")
            if vlink_df is not None:
                st.download_button(
                    "Download Verification Report",
                    to_excel_bytes(vlink_df, sheet_name="Verification"),
                    "Deliveries_Verification.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

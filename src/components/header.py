import os
import base64
import streamlit as st


from datetime import datetime, timedelta
from src.components.clock import get_clock_html


def render_header(right_slot_callback=None):
    """Modern command-center header with exact user-requested styling."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 0px; justify-content: space-between; width: 100%;">
            <h1 class="hub-title" id="deen-ops-terminal-v10-0" aria-labelledby=":r9:" style="margin: 0px;">
                <span id=":r9:">DEEN OPS Terminal <span style="color: rgb(29, 78, 216);">v10.0</span></span>
            </h1>
        </div>
        <p style="color: var(--text-muted); margin-bottom: -10px; font-size: 1rem;">Operational Command & Business Intelligence Center</p>
        """,
        unsafe_allow_html=True
    )
    if right_slot_callback:
        with st.container():
            right_slot_callback()


def render_app_banner():
    """Renders a premium visual banner for the application with integrated clock, title, and sync status."""
    banner_path = os.path.join("assets", "app_banner.png")
    clock_html = get_clock_html()
    
    sync_label = "Checking status..."
    if st.session_state.get("live_sync_time"):
        diff = datetime.now() - st.session_state.live_sync_time
        mins = int(diff.total_seconds() / 60)
        sync_label = "Synced: Just now" if mins < 1 else f"Synced: {mins}m ago"
    elif st.session_state.get("wc_sync_mode") == "Operational Cycle":
         sync_label = "Syncing with WooCommerce..."

    # v15.0: Dynamic Holiday Awareness Logic
    holiday_banner_html = ""
    is_holiday_merge = False
    
    # Check if we are in Operational Cycle and if a merge is active
    if st.session_state.get("wc_sync_mode") == "Operational Cycle":
        curr_slot = st.session_state.get("wc_curr_slot")
        if curr_slot and len(curr_slot) == 2:
            start, end = curr_slot
            # If the duration is more than 28 hours, it's likely a holiday merge (normal shift is ~24h)
            if (end - start).total_seconds() > 100800: # 28 hours
                is_holiday_merge = True
                merge_date = (start + timedelta(hours=12)).strftime("%a, %d %b")
                holiday_banner_html = f"""
                    <div style="position: absolute; top: 15px; left: 40px; z-index: 10; display: flex; align-items: center; gap: 8px; background: rgba(59, 130, 246, 0.2); backdrop-filter: blur(10px); padding: 6px 14px; border-radius: 20px; border: 1px solid rgba(59, 130, 246, 0.4); animation: pulse 2s infinite;">
                        <span style="font-size: 0.9rem;">🌙</span>
                        <span style="color: #60a5fa; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase;">Holiday Merge Active</span>
                        <span style="color: white; font-size: 0.7rem; font-weight: 600;">(Incl. {merge_date})</span>
                    </div>
                    <style>
                    @keyframes pulse {{
                        0% {{ transform: scale(1); opacity: 0.9; }}
                        50% {{ transform: scale(1.02); opacity: 1; }}
                        100% {{ transform: scale(1); opacity: 0.9; }}
                    }}
                    </style>
                """

    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
<style>
.app-banner-wrapper {{ position: relative; width: 100%; height: 220px; border-radius: 12px; overflow: hidden; margin-bottom: 24px; box-shadow: var(--card-shadow); }}
.app-banner-overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, rgba(15, 23, 42, 0.8) 0%, rgba(15, 23, 42, 0.1) 100%); display: flex; align-items: center; justify-content: space-between; padding: 0 40px; z-index: 2; }}
.app-banner-title-area {{ width: auto; z-index: 5; margin-right: 20px; }}
.app-banner-title {{ color: white; font-size: 1.8rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px; }}
.app-banner-subtitle {{ color: rgba(255, 255, 255, 0.7); font-size: 0.95rem; }}
.app-banner-clock-area {{ background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(8px); padding: 10px 18px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.15); z-index: 10; text-align: right; min-width: max-content; }}

@media (max-width: 800px) {{
    .app-banner-wrapper {{ height: auto; min-height: 180px; }}
    .app-banner-overlay {{ flex-direction: column; align-items: flex-start; justify-content: center; padding: 25px 20px; gap: 15px; position: static; background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(15, 23, 42, 0.5) 100%); }}
    .app-banner-img {{ display: none; }} /* Hide or dim on very small screens to avoid weird scaling */
    .app-banner-title {{ font-size: 1.4rem; }}
    .app-banner-subtitle {{ font-size: 0.85rem; }}
    .app-banner-clock-area {{ text-align: left; background: rgba(0,0,0,0.2); padding: 12px !important; margin-top: 5px; width: 100%; box-sizing: border-box; }}
}}
</style>
<div class="app-banner-wrapper">
<img src="data:image/png;base64,{b64}" class="app-banner-img" style="width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; z-index: 1;">
{holiday_banner_html}
<div class="app-banner-overlay">
<div class="app-banner-title-area">
<div class="app-banner-title">DEEN OPS Terminal</div>
<div class="app-banner-subtitle">Advanced Operational Analytics & Strategic Data Pilot</div>
</div>
<div class="app-banner-clock-area">
{clock_html}
<div style="margin-top: 6px; color: rgba(255,255,255,0.6); font-size: 0.75rem; font-family: sans-serif; letter-spacing: 0.05em; font-weight: 600;">🔄 {sync_label.upper()}</div>
</div>
</div>
</div>""",
            unsafe_allow_html=True
        )


def render_banner_mode_controls():
    """Renders operational mode radio buttons at the bottom-left of the banner area."""
    nav_mode = st.session_state.get("wc_nav_mode", "Today")
    mode_options = ["Last Day", "Active", "Queue"]
    mode_to_state = {"Last Day": "Prev", "Active": "Today", "Queue": "Backlog"}
    state_to_mode = {v: k for k, v in mode_to_state.items()}
    current_idx = mode_options.index(state_to_mode.get(nav_mode, "Active"))

    # Single CSS block for positioning the controls at BOTTOM LEFT
    st.markdown(f"""
        <style>
        .banner-controls-shelf {{
            margin-top: -85px;
            margin-bottom: 45px;
            margin-left: 35px;
            z-index: 100;
            position: relative;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            pointer-events: none;
        }}
        .banner-controls-shelf > div {{
            pointer-events: auto;
            background: rgba(15, 23, 42, 0.5);
            backdrop-filter: blur(12px);
            padding: 4px 12px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
        }}
        .banner-controls-shelf label p {{
            color: white !important;
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        /* Remove extra space in the radio group */
        .banner-controls-shelf [data-testid="stRadio"] {{
            margin-bottom: -15px;
        }}
        @media (max-width: 800px) {{
            .banner-controls-shelf {{
                margin-top: 10px;
                margin-bottom: 25px;
                margin-left: 0;
                justify-content: center;
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="banner-controls-shelf">', unsafe_allow_html=True)
        
        # Use a narrower column for the radio buttons
        c1, _ = st.columns([1.5, 3])
        with c1:
            selected_mode = st.radio(
                "Op Mode",
                mode_options,
                index=current_idx,
                horizontal=True,
                key="banner_op_mode_radio",
                label_visibility="collapsed"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

    new_nav = mode_to_state[selected_mode]
    if new_nav != nav_mode:
        st.session_state.wc_nav_mode = new_nav
        st.rerun()

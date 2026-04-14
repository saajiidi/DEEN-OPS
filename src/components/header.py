import os
import base64
import streamlit as st


from datetime import datetime
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
    """Renders a premium visual banner for the application with integrated clock and title."""
    banner_path = os.path.join("assets", "app_banner.png")
    clock_html = get_clock_html()
    
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""<div style="position: relative; width: 100%; height: 220px; border-radius: 12px; overflow: hidden; margin-bottom: 24px; box-shadow: var(--card-shadow);">
<img src="data:image/png;base64,{b64}" style="width: 100%; height: 100%; object-fit: cover;">
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, rgba(15, 23, 42, 0.8) 0%, rgba(15, 23, 42, 0.2) 100%); display: flex; align-items: center; padding: 0 40px;">
<div style="width: 100%;">
<div style="color: white; font-size: 1.8rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px;">DEEN OPS Terminal</div>
<div style="color: rgba(255, 255, 255, 0.7); font-size: 0.95rem;">Advanced Operational Analytics & Strategic Data Pilot</div>
</div>
</div>
<div style="position: absolute; top: 20px; right: 30px; background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(8px); padding: 6px 16px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); z-index: 10;">
{clock_html}
</div>
</div>""",
            unsafe_allow_html=True
        )


def render_banner_mode_controls():
    """Renders operational mode radio and sync status at bottom-right of banner area."""
    nav_mode = st.session_state.get("wc_nav_mode", "Today")
    mode_options = ["Last Day", "Active", "Queue"]
    mode_to_state = {"Last Day": "Prev", "Active": "Today", "Queue": "Backlog"}
    state_to_mode = {v: k for k, v in mode_to_state.items()}
    current_idx = mode_options.index(state_to_mode.get(nav_mode, "Active"))

    sync_label = "Just now"
    if st.session_state.get("live_sync_time"):
        diff = datetime.now() - st.session_state.live_sync_time
        mins = int(diff.total_seconds() / 60)
        sync_label = "Just now" if mins < 1 else f"{mins}m ago"

    # Single CSS block for positioning the controls EXACTLY at bottom right of the banner
    st.markdown(f"""
        <style>
        .banner-controls-shelf {{
            margin-top: -95px;
            margin-bottom: 55px;
            z-index: 100;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            pointer-events: none; /* Let clicks pass through to child widgets */
        }}
        .banner-controls-shelf > div {{
            pointer-events: auto; /* Enable clicks for the selector box */
            background: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .banner-controls-shelf label p {{
            color: white !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        # Outer shelf for positioning
        st.markdown('<div class="banner-controls-shelf">', unsafe_allow_html=True)
        
        # Internal layout using columns to match the shelf style
        c1, c2 = st.columns([2.8, 1])
        with c1:
            selected_mode = st.radio(
                "Op Mode",
                mode_options,
                index=current_idx,
                horizontal=True,
                key="banner_op_mode_radio",
                label_visibility="collapsed"
            )
        with c2:
            st.markdown(f'<div style="color:rgba(255,255,255,0.7); font-size:0.8rem; white-space:nowrap; margin-top:5px;">🔄 {sync_label}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    new_nav = mode_to_state[selected_mode]
    if new_nav != nav_mode:
        st.session_state.wc_nav_mode = new_nav
        st.rerun()

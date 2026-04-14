import os
import base64
import streamlit as st


def render_header(right_slot_callback=None):
    """Modern command-center header with exact user-requested styling."""
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 0px; justify-content: space-between; width: 100%;">
            <h1 class="hub-title" id="deen-ops-terminal-v10-0" aria-labelledby=":r9:" style="margin: 0px;">
                <span id=":r9:">DEEN OPS Terminal <span style="color: rgb(29, 78, 216);">v10.0</span></span>
            </h1>
        </div>
        <p style="color: var(--text-muted); margin-bottom: 24px; font-size: 1rem;">Operational Command & Business Intelligence Center</p>
        """,
        unsafe_allow_html=True
    )
    if right_slot_callback:
        with st.container():
            right_slot_callback()


def render_app_banner():
    """Renders a premium visual banner for the application."""
    banner_path = os.path.join("assets", "app_banner.png")
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <div style="position: relative; width: 100%; height: 200px; border-radius: 12px; overflow: hidden; margin-bottom: 24px; box-shadow: var(--card-shadow);">
                <img src="data:image/png;base64,{b64}" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(90deg, rgba(15, 23, 42, 0.7) 0%, rgba(15, 23, 42, 0) 100%); display: flex; align-items: center; padding: 0 40px;">
                    <div>
                        <div style="color: white; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 4px;">DEEN OPS Terminal</div>
                        <div style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem;">Advanced Operational Analytics & Strategic Data Pilot</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

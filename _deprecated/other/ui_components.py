# ui_components.py - Streamlit UI components

import streamlit as st
import json
import os
from datetime import datetime
from config import FEEDBACK_DIR

def render_sidebar():
    """Sidebar for feedback and debugging."""
    with st.sidebar:
        st.header("💬 Feedback & Debug")
        comment = st.text_area("Report Issues:", placeholder="Category 'Polo' is incorrect...")
        if st.button("Submit Report"):
            feedback_file = os.path.join(FEEDBACK_DIR, "user_feedback.json")
            entry = {"timestamp": datetime.now().isoformat(), "comment": comment}
            try:
                data = []
                if os.path.exists(feedback_file):
                    with open(feedback_file, "r") as f: data = json.load(f)
                data.append(entry)
                with open(feedback_file, "w") as f: json.dump(data, f, indent=4)
                st.success("Feedback saved!")
            except: st.error("Failed to save.")
        
        st.divider()
        if st.checkbox("View System Logs"):
            log_path = os.path.join(FEEDBACK_DIR, "system_logs.json")
            if os.path.exists(log_path):
                with open(log_path, "r") as f: st.json(json.load(f)[-10:])
            else: st.info("No logs available.")

def render_footer(logo_b64):
    """Sticky footer with logo and attribution."""
    footer_html = f"""
    <div class="sticky-footer">
        <div class="footer-content-inner">
            <span>© {datetime.now().year} Sajid Islam. All rights reserved. | Powered by</span>
            <div class="brand-wrapper">
                <img src="data:image/png;base64,{logo_b64}" class="small-logo">
                <span style="font-weight: 600; color: #1a1a1b;">DEEN Commerce</span>
            </div>
        </div>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

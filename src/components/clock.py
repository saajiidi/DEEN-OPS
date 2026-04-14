import streamlit as st
from datetime import datetime, timedelta, timezone

def get_clock_html():
    """Returns the compact, single-line JavaScript clock HTML string."""
    tz_bd = timezone(timedelta(hours=6))
    now_bd = datetime.now(tz_bd)
    return f"""<div style="text-align: right; line-height: 1.5; color: white; font-family: sans-serif;">
<span id="header-clock-time" style="font-size: 1.05rem; font-weight: 700; letter-spacing: -0.3px;">{now_bd.strftime('%I:%M:%S %p')}</span>
<span style="color: rgba(255,255,255,0.4); margin: 0 10px; font-weight: 300;">|</span>
<span id="header-clock-date" style="font-size: 0.9rem; color: rgba(255,255,255,0.8); font-weight: 500;">{now_bd.strftime('%A, %B %d')}</span>
</div>
<script>
(function() {{
if (window.headerClockInterval) clearInterval(window.headerClockInterval);
function updateClock() {{
const timeEl = document.getElementById('header-clock-time');
const dateEl = document.getElementById('header-clock-date');
if (!timeEl) return;
const now = new Date();
const bdTime = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + (6 * 3600000));
timeEl.innerHTML = bdTime.toLocaleTimeString('en-US', {{
hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
}});
if (dateEl) {{
dateEl.innerHTML = bdTime.toLocaleDateString('en-US', {{
weekday: 'long', month: 'long', day: '2-digit'
}});
}}
}}
updateClock();
window.headerClockInterval = setInterval(updateClock, 1000);
}})();
</script>"""

def render_dynamic_clock(sync_time=None):
    """Renders a compact, high-fidelity JavaScript clock for the header (Single Line)."""
    st.markdown(get_clock_html(), unsafe_allow_html=True)

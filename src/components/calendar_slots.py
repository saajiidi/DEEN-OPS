import streamlit as st
import calendar
from datetime import datetime, date, timedelta
from src.state.persistence import save_state

def render_operational_slots_calendar():
    """
    Modern UI-UX 'Material Card' tile calendar for operational holiday splicing.
    """
    st.markdown("""
        <style>
        /* Modern Tile Grid Styling */
        div[data-testid="stExpander"] .stButton button {
            background-color: white !important;
            border: 1px solid rgba(0,0,0,0.05) !important;
            border-radius: 8px !important;
            color: #1e293b !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            aspect-ratio: 1 / 1 !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-bottom: 4px !important;
        }
        
        div[data-testid="stExpander"] .stButton button:hover {
            border-color: #3b82f6 !important;
            background-color: #f8fafc !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
            transform: translateY(-2px);
        }

        /* Highlight for current month indicator */
        .cal-nav-text {
            font-size: 0.9rem;
            font-weight: 800;
            color: #1e293b;
            text-align: center;
            margin: 0;
            padding-top: 6px;
        }

        /* Special Tile States */
        div[data-testid="stExpander"] .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            border: none !important;
        }
        
        /* Holiday/Default State Indicator Icons */
        .status-dot {
            height: 6px;
            width: 6px;
            background-color: #ef4444;
            border-radius: 50%;
            display: inline-block;
            margin-left: 2px;
        }
        
        .header-tile {
            font-size: 0.7rem;
            font-weight: 700;
            color: #94a3b8;
            text-align: center;
            text-transform: uppercase;
            padding-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    if "operational_holidays" not in st.session_state:
        st.session_state.operational_holidays = []
    
    # Month Navigation State
    if "cal_year" not in st.session_state:
        st.session_state.cal_year = datetime.now().year
    if "cal_month" not in st.session_state:
        st.session_state.cal_month = datetime.now().month

    # Premium Header
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 1, 4, 1])
    with h_col1:
        if st.button("←", key="nav_p", help="Prev Month"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month < 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            st.rerun()
    with h_col2:
        if st.button("•", key="nav_t", help="Today"):
            st.session_state.cal_year = datetime.now().year
            st.session_state.cal_month = datetime.now().month
            st.rerun()
    with h_col3:
        m_name = calendar.month_name[st.session_state.cal_month]
        st.markdown(f"<p class='cal-nav-text'>{m_name} '{str(st.session_state.cal_year)[2:]}</p>", unsafe_allow_html=True)
    with h_col4:
        if st.button("→", key="nav_n", help="Next Month"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month > 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            st.rerun()

    # Calendar Grid
    cal = calendar.Calendar(firstweekday=calendar.SATURDAY)
    m_days = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)
    
    # Weekday Headers
    cols = st.columns(7)
    days = ["Sa", "Su", "Mo", "Tu", "We", "Th", "Fr"]
    for i, d in enumerate(days):
        cols[i].markdown(f"<div class='header-tile'>{d}</div>", unsafe_allow_html=True)
    
    hols = st.session_state.operational_holidays
    t_day = date.today()
    
    for week in m_days:
        cols = st.columns(7)
        for i, d in enumerate(week):
            if d == 0:
                cols[i].write("")
                continue
            
            c_date = date(st.session_state.cal_year, st.session_state.cal_month, d)
            is_fri = c_date.weekday() == 4
            d_str = c_date.strftime("%Y-%m-%d")
            is_hol = d_str in hols
            is_today = c_date == t_day
            
            # Labeling
            label = str(d)
            if is_hol: label = f"{d} 🛑"
            elif is_fri: label = f"{d} ☁️"
            
            if is_today:
                label = f"• {label}"
            
            # Tile Interaction
            if cols[i].button(label, key=f"tile_{d_str}", use_container_width=True, type="primary" if (is_fri or is_hol) else "secondary"):
                if d_str in hols:
                    hols.remove(d_str)
                else:
                    hols.append(d_str)
                st.session_state.operational_holidays = hols
                save_state()
                # Clear refresh flags
                st.session_state.wc_curr_df = None
                st.session_state.wc_prev_df = None
                st.rerun()

    st.markdown("""
        <div style='background: rgba(59, 130, 246, 0.04); padding: 12px; border-radius: 10px; border: 1px solid rgba(59, 130, 246, 0.1); margin-top: 10px;'>
            <div style='display: flex; gap: 10px; font-size: 0.75rem;'>
                <span>☁️ <b>Fri</b> (Default)</span>
                <span>🛑 <b>Manual</b> Holiday</span>
            </div>
            <div style='font-size: 0.7rem; color: #64748b; margin-top: 4px;'>• Today indicator</div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Reset Month to Defaults", use_container_width=True, type="secondary"):
        prefix = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}"
        st.session_state.operational_holidays = [h for h in hols if not h.startswith(prefix)]
        save_state()
        st.rerun()

    st.divider()
    # Force Merge Overrides using standard Material cards look
    c_merge = st.toggle("Force 48h (Active)", value=st.session_state.get("override_merge_current", False))
    p_merge = st.toggle("Force 48h (Historical)", value=st.session_state.get("override_merge_previous", False))
    
    if c_merge != st.session_state.get("override_merge_current", False) or \
       p_merge != st.session_state.get("override_merge_previous", False):
        st.session_state.override_merge_current = c_merge
        st.session_state.override_merge_previous = p_merge
        st.session_state.wc_curr_df = None
        st.session_state.wc_prev_df = None
        st.rerun()

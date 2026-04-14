import streamlit as st

from src.config.ui_config import APP_TITLE, APP_VERSION


def inject_base_styles():
    st.markdown(
        f"""
        <style>
        :root {{
            --primary: var(--primary-color, #1d4ed8);
            --primary-glow: rgba(29, 78, 216, 0.1);
            --surface: var(--background-color, #f8fafc);
            --border: rgba(128, 128, 128, 0.15);
            --text-main: var(--text-color, #0f172a);
            --text-muted: #64748b;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --step-surface: var(--background-color, #f8fafc);
            --step-text: var(--text-color, #0f172a);
            --step-active-bg: var(--secondary-background-color, rgba(29, 78, 216, 0.05));
            --action-surface: var(--secondary-background-color, rgba(255, 255, 255, 0.96));
        }}

        /* Modern Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}

        .stApp {{
            background: var(--background-color);
        }}

        .hub-footer {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: var(--background-color);
            color: var(--text-color);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            border-top: 1px solid rgba(128, 128, 128, 0.2);
            z-index: 999;
        }}
        .hub-footer a {{
            color: inherit;
            text-decoration: none;
            font-weight: 500;
        }}
        /* Extra padding for main content so it doesn't get hidden by fixed footer */
        .main .block-container {{
            padding-bottom: 80px !important;
        }}
        .deen-logo-small {{
            vertical-align: middle;
            margin-right: 6px;
            border-radius: 4px;
        }}
        .hub-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(29, 78, 216, 0.02);
            border-left: 4px solid var(--primary);
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            margin-bottom: 24px;
            border-radius: 0 12px 12px 0;
        }}

        /* Remove the top gap without touching the sidebar toggle */
        .main .block-container {{
            padding-top: 0 !important;
            margin-top: -1.75rem !important;
            padding-bottom: 80px !important;
        }}
        .hub-subtitle {{
            margin: 0;
            color: var(--text-muted);
            font-size: 0.95rem;
        }}
        .hub-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: var(--card-shadow);
            transition: all 0.2s ease;
        }}
        .hub-card:hover {{
            transform: translateY(-2px);
            border-color: var(--primary);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}




        /* Hub Title Style (Premium) */
        .hub-title {{
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
            color: var(--text-main) !important;
            margin: 0px !important;
        }}

        /* Notification Popover Styling */
        div[data-testid="stPopover"] button {{
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 20px !important;
            padding: 4px 16px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            transition: all 0.3s ease !important;
        }}
        div[data-testid="stPopover"] button:hover {{
            border-color: var(--primary) !important;
            box-shadow: 0 4px 12px var(--primary-glow) !important;
            transform: translateY(-1px);
        }}

        /* 3. Action Glow for success/primary steps */
        @keyframes success-pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}
        div[data-testid="stDownloadButton"] button {{
            animation: success-pulse 2s infinite;
            border: 1px solid #10b981 !important;
            transition: all 0.2s ease !important;
        }}
        div[data-testid="stDownloadButton"] button:hover {{
            transform: scale(1.02);
            background: #059669 !important;
            color: white !important;
        }}

        /* Global button hover scaling */
        button[kind="secondary"]:hover, button[kind="primary"]:hover {{
            transform: scale(1.01);
            transition: all 0.2s ease !important;
        }}

        /* Premium Tab Styling */
        div[data-testid="stTab"] button {{
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            color: #64748b !important;
            transition: all 0.3s ease !important;
            border: none !important;
            background: transparent !important;
            padding: 10px 20px !important;
        }}
        div[data-testid="stTab"] button:hover {{
            color: #1d4ed8 !important;
            background: rgba(29, 78, 216, 0.04) !important;
            border-radius: 8px 8px 0 0 !important;
        }}
        div[data-testid="stTab"] button[aria-selected="true"] {{
            color: #1d4ed8 !important;
            border-bottom: 2px solid #1d4ed8 !important;
        }}

        @media (max-width: 900px) {{
            .hub-welcome-banner {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .hub-welcome-status {{
                text-align: left;
                width: 100%;
                margin-top: 4px;
            }}
            .block-container {{
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                margin-top: -2.5rem !important;
            }}
            .hub-title {{
                font-size: 1.2rem !important;
                line-height: 1.2;
            }}
            .hub-subtitle {{
                font-size: 0.8rem !important;
            }}
            .hub-card {{
                padding: 10px;
                border-radius: 8px;
            }}
            /* Metric Font Scaling for Small Screens */
            div[data-testid="stMetricValue"] {{
                font-size: 1.2rem !important;
            }}
            div[data-testid="stMetricLabel"] {{
                font-size: 0.75rem !important;
            }}
            /* Compact Tabs on Mobile */
            div[data-testid="stTab"] button {{
                padding: 8px 12px !important;
                font-size: 0.8rem !important;
            }}
        }}

        /* Hide Plotly legends on mobile and small screens */
        @media (max-width: 900px) {{
            .js-plotly-plot .legend, .js-plotly-plot .legendtoggle, .js-plotly-plot .legend-bg, .js-plotly-plot .legend-layer {{
                display: none !important;
            }}
        }}

        /* Chat UI Enhancements */
        .stChatMessage {{
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.05)) !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            padding: 1.2rem !important;
            margin-bottom: 1rem !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
            transition: transform 0.2s ease !important;
        }}
        .stChatMessage:hover {{
            transform: translateX(4px);
            border-color: var(--primary) !important;
        }}
        .stChatMessage [data-testid="stChatMessageContent"] {{
            font-size: 1.05rem !important;
            line-height: 1.6 !important;
        }}
        /* Assistant Message Slight Glow */
        .stChatMessage[data-testid="stChatMessageAssistant"] {{
            border-left: 4px solid var(--primary) !important;
            background: linear-gradient(90deg, var(--primary-glow) 0%, transparent 100%) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

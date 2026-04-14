# utils.py - Helper functions and event logging

import os
import base64
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from config import LOGO_PNG, FEEDBACK_DIR, SALES_CATEGORY_MAPPING, STOCK_CATEGORY_MAPPING, COLUMN_ALIAS_MAPPING

os.makedirs(FEEDBACK_DIR, exist_ok=True)

def load_logo():
    """Loads logo as base64 string from config path."""
    if os.path.exists(LOGO_PNG):
        try:
            with open(LOGO_PNG, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: pass
    return ""

def log_event(event_type, details):
    """Logs system events to JSON."""
    log_file = os.path.join(FEEDBACK_DIR, "system_logs.json")
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "details": details
    }
    try:
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f: logs = json.load(f)
        logs.append(entry)
        with open(log_file, "w") as f: json.dump(logs[-100:], f, indent=4)
    except: pass

def get_product_category(name, mode="Sales Performance"):
    """Categorizes product based on keywords or lambdas from mapping."""
    name_str = str(name).lower()
    mapping = STOCK_CATEGORY_MAPPING if mode == "Stock Count" else SALES_CATEGORY_MAPPING
    
    for cat, check in mapping.items():
        if callable(check):
            if check(name_str): return cat
        elif any(kw.lower() in name_str for kw in check):
            return cat
    return 'Others'

def find_columns(df):
    """Auto-detects columns from dataframe based on aliases."""
    found = {}
    actual_cols = list(df.columns)
    lower_cols = [c.strip().lower() for c in actual_cols]
    
    for key, aliases in COLUMN_ALIAS_MAPPING.items():
        # Exact match
        for alias in aliases:
            if alias in lower_cols:
                found[key] = actual_cols[lower_cols.index(alias)]
                break
        # Partial match
        if key not in found:
            for i, col in enumerate(lower_cols):
                if any(alias in col for alias in aliases):
                    found[key] = actual_cols[i]
                    break
    return found

def apply_custom_styles():
    """Applies premium CSS styles to the dashboard."""
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stMetric { 
            background-color: #ffffff; 
            padding: 20px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }
        .stButton>button { 
            width: 100%; border-radius: 8px; height: 3.2em; background-color: #007bff; color: white; font-weight: 600; transition: all 0.3s ease;
        }
        .stButton>button:hover { background-color: #0056b3; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.05); background: white; border-radius: 10px; margin-bottom: 1rem; }
        .sticky-footer {
            position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(255, 255, 255, 0.95); color: #6c757d; text-align: center;
            padding: 15px 0; border-top: 1px solid #e9ecef; z-index: 999; font-size: 0.85rem; backdrop-filter: blur(8px); box-shadow: 0 -4px 20px rgba(0,0,0,0.04);
        }
        .footer-content-inner { display: flex; align-items: center; justify-content: center; gap: 8px; }
        .brand-wrapper { display: flex; align-items: center; gap: 2px; }
        .small-logo { height: 22px; width: auto; filter: grayscale(20%); }
        .block-container { padding-bottom: 100px !important; }
        </style>
        """, unsafe_allow_html=True)

# analytics.py - Core data processing logic

import pandas as pd
from datetime import datetime
from utils import get_product_category

def process_analytics(df, mapping, mode="Sales Performance"):
    """Core data processing and metric calculation."""
    df = df.copy()
    
    # 1. Clean Data
    df['Clean_Name'] = df[mapping['name']].fillna('Unknown').astype(str)
    df = df[~df['Clean_Name'].str.contains('Choose Any', case=False, na=False)]
    
    cost_col = mapping.get('cost')
    qty_col = mapping.get('qty')
    
    df['Clean_Cost'] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0) if cost_col else 0
    df['Clean_Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0) if qty_col else 0
    df.loc[df['Clean_Qty'] < 0, 'Clean_Qty'] = 0
    
    df['Total Amount'] = df['Clean_Cost'] * df['Clean_Qty']
    df['Category'] = df['Clean_Name'].apply(lambda n: get_product_category(n, mode=mode))
    
    # 2. Timeframe Detection
    timeframe = ""
    if mapping.get('date') and mapping['date'] in df.columns:
        try:
            dates = pd.to_datetime(df[mapping['date']], errors='coerce').dropna()
            if not dates.empty:
                if dates.dt.to_period('M').nunique() == 1:
                    timeframe = dates.iloc[0].strftime("%B_%Y")
                else:
                    timeframe = f"{dates.min().strftime('%d%b')}_to_{dates.max().strftime('%d%b_%y')}"
        except: timeframe = "Report"

    # 3. Aggregations
    summary = df.groupby('Category').agg({'Clean_Qty': 'sum', 'Total Amount': 'sum'}).reset_index()
    summary.columns = ['Category', 'Total Qty', 'Total Amount']
    
    t_rev = summary['Total Amount'].sum()
    t_qty = summary['Total Qty'].sum()
    
    drilldown = df.groupby(['Category', 'Clean_Cost']).agg({'Clean_Qty': 'sum', 'Total Amount': 'sum'}).reset_index()
    drilldown.columns = ['Category', 'Price', 'Qty', 'Total Amount']
    
    top_items = df.groupby('Clean_Name').agg({'Clean_Qty': 'sum', 'Total Amount': 'sum', 'Category': 'first'}).reset_index()
    top_items.columns = ['Product Name', 'Total Qty', 'Total Amount', 'Category']
    top_items = top_items.sort_values('Total Amount', ascending=False)
    
    # 4. Basket Metrics
    avg_basket_value = 0
    order_groups_count = 0
    group_cols = [c for c in [mapping.get('order_id'), mapping.get('phone')] if c and c in df.columns]
    
    if group_cols:
        order_groups = df.groupby(group_cols).agg({'Total Amount': 'sum'})
        avg_basket_value = order_groups['Total Amount'].mean()
        order_groups_count = len(order_groups)
        
    return {
        'drilldown': drilldown,
        'summary': summary,
        'top_items': top_items,
        'timeframe': timeframe,
        'avg_basket_value': avg_basket_value,
        'total_qty': t_qty,
        'total_rev': t_rev,
        'total_orders': order_groups_count
    }

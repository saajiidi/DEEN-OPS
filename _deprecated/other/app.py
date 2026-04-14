# app.py - Smart Analytics Hub
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

# Import modular components
import config
from utils import load_logo, apply_custom_styles, log_event, find_columns
from analytics import process_analytics
from ui_components import render_sidebar, render_footer
from woocommerce_client import get_wc_api, fetch_wc_orders, fetch_wc_products, API

def main():
    st.set_page_config(page_title="Analytics Hub", page_icon="📊", layout="wide")
    apply_custom_styles()
    
    logo_b64 = load_logo()
    render_sidebar()
    
    st.title("🚀 Smart Analytics Hub")
    
    st.sidebar.title("🔌 Data Source")
    src_mode = st.sidebar.radio("Choose Source", ["Excel/CSV Upload", "WooCommerce API"])
    
    # Use session state to persist data between reruns
    if 'data' not in st.session_state:
        st.session_state['data'] = None
    
    if src_mode == "Excel/CSV Upload":
        uploaded_file = st.file_uploader(f"Upload {mode} Data (Excel or CSV)", type=['xlsx', 'csv'])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_loaded = pd.read_csv(uploaded_file)
                else:
                    df_loaded = pd.read_excel(uploaded_file)
                if mode == "Stock Count" and 'Type' in df_loaded.columns:
                    df_loaded = df_loaded[df_loaded['Type'].str.lower().isin(['variation', 'simple'])]
                
                st.session_state['data'] = df_loaded
            except Exception as e:
                st.error(f"File Error: {e}")
    else:
        # WooCommerce API Configuration
        with st.expander("🔑 WooCommerce API Connection", expanded=True):
            wc_defaults = st.secrets.get("woocommerce", {})
            if wc_defaults:
                st.info(f"📍 **Target Store:** {wc_defaults.get('store_url', 'Not Set')}")
                
                # Selection for filter types
                if mode == "Sales Performance":
                    f_col1, f_col2 = st.columns(2)
                    filter_type = f_col1.radio("🔌 Sync Criteria", ["Date Range", "Last Shipped Orders", "Order No. Range"], horizontal=True)
                    
                    pull_kwargs = {"filter_type": filter_type}
                    
                    if filter_type == "Date Range":
                        dr1, dr2 = st.columns(2)
                        pull_kwargs["start_date"] = dr1.date_input("Start Date", value=datetime.now())
                        pull_kwargs["end_date"] = dr2.date_input("End Date", value=datetime.now())
                    elif filter_type == "Last Shipped Orders":
                        pull_kwargs["limit"] = st.selectbox("Number of Orders", [25, 40, 50], index=0)
                    else:
                        c1, c2 = st.columns(2)
                        pull_kwargs["min_id"] = c1.number_input("From Order ID", value=0, step=1)
                        pull_kwargs["max_id"] = c2.number_input("To Order ID", value=999999, step=1)
                else:
                    pull_kwargs = {"filter_type": "Products"}
                    
                if st.button("🔗 Pull Live Data"):
                    try:
                        with st.spinner("Connecting to WooCommerce..."):
                            wcapi = get_wc_api(
                                wc_defaults.get("store_url"), 
                                wc_defaults.get("consumer_key"), 
                                wc_defaults.get("consumer_secret")
                            )
                            if mode == "Sales Performance":
                                df_loaded = fetch_wc_orders(wcapi, **pull_kwargs)
                            else:
                                df_loaded = fetch_wc_products(wcapi)
                        
                        if df_loaded is not None and not df_loaded.empty:
                            st.session_state['data'] = df_loaded
                            st.success(f"Successfully pulled {len(df_loaded)} records from {wc_defaults.get('store_url')}")
                        else:
                            st.info("No data found for the selected criteria.")
                    except Exception as e:
                        st.error(f"API Connection Error: {e}")
            else:
                st.error("⚠️ WooCommerce credentials not found in secrets.toml!")
    
    # Process the data if it exists in session state
    df = st.session_state['data']
    if df is not None and not df.empty:
        try:
            st.info(f"📊 Analyzing data with {len(df)} records.")
            
            # --- Continue with existing Column Mapping ---
            auto_cols = find_columns(df)
            all_cols = list(df.columns)
            mandatory_keys = ['name', 'cost', 'qty']
            is_mapped = all(k in auto_cols for k in mandatory_keys)
            
            with st.expander("🛠️ Column Mapping Configuration", expanded=not is_mapped):
                if not is_mapped:
                    st.warning("⚠️ System couldn't auto-detect all mandatory columns. Please map them manually.")
                else:
                    st.info("✨ Auto-detected columns. You can adjust them below.")
                
                mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
                
                def get_idx(key):
                    return all_cols.index(auto_cols[key]) if key in auto_cols else 0

                m_name = mc1.selectbox("Product Name", all_cols, index=get_idx('name'))
                m_cost = mc2.selectbox("Price/Cost", all_cols, index=get_idx('cost'))
                m_qty = mc3.selectbox("Quantity", all_cols, index=get_idx('qty'))
                m_date = mc4.selectbox("Date (Opt)", ["None"] + all_cols, index=get_idx('date')+1 if 'date' in auto_cols else 0)
                m_order = mc5.selectbox("Order ID (Opt)", ["None"] + all_cols, index=get_idx('order_id')+1 if 'order_id' in auto_cols else 0)
                m_phone = mc6.selectbox("Phone (Opt)", ["None"] + all_cols, index=get_idx('phone')+1 if 'phone' in auto_cols else 0)
            
            mapping = {
                'name': m_name, 'cost': m_cost, 'qty': m_qty,
                'date': m_date if m_date != "None" else None,
                'order_id': m_order if m_order != "None" else None,
                'phone': m_phone if m_phone != "None" else None
            }
            
            with st.expander("🔍 Preview Data"):
                preview_df = df.head(10).copy()
                preview_df.index = range(1, len(preview_df) + 1)
                st.dataframe(preview_df, use_container_width=True)

            if st.button("Generate Analytics"):
                # Run the analytics engine
                results = process_analytics(df, mapping, mode=mode)
                
                # 3. Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                if mode == "Sales Performance":
                    m1.metric("Orders", f"{results['total_orders']:,.0f}" if results['total_orders'] > 0 else "N/A")
                    m2.metric("Units Sold", f"{results['total_qty']:,.0f}")
                    m3.metric("Total Revenue", f"TK {results['total_rev']:,.2f}")
                    m4.metric("Avg Basket (TK)", f"TK {results['avg_basket_value']:,.2f}" if results['avg_basket_value'] > 0 else "N/A")
                else:
                    m1.metric("Total SKU Count", f"{len(df):,.0f}")
                    m2.metric("Total Stock Qty", f"{results['total_qty']:,.0f}")
                    m3.metric("Total Stock Value", f"TK {results['total_rev']:,.2f}")
                    m4.metric("Avg Qty/SKU", f"{results['total_qty']/len(df):,.1f}" if len(df) > 0 else "N/A")

                st.divider()
                
                # 4. Visuals (Charts)
                v1, v2 = st.columns(2)
                
                # Sort once for consistent color sequence
                summ_sorted = results['summary'].sort_values('Total Amount', ascending=False)
                # Premium Color Palette
                color_seq = ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#3a86ff', '#8338ec', '#ff006e', '#fb5607', '#ffbe0b']
                label_prefix = "Revenue" if mode == "Sales Performance" else "Value"
                
                # Doughnut Chart with Static Labels
                pie_fig = px.pie(summ_sorted, values='Total Amount', names='Category', hole=0.5, 
                                 title=f'{label_prefix} Share by Category', color_discrete_sequence=color_seq)
                pie_fig.update_traces(textposition='inside', textinfo='percent+label')
                v1.plotly_chart(pie_fig, use_container_width=True)
                
                # Bar Chart with Labels
                bar_fig = px.bar(summ_sorted, x='Category', y='Total Qty', color='Category', 
                                 title='Volume Breakdown by Category', color_discrete_sequence=color_seq,
                                 text='Total Qty')
                bar_fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
                bar_fig.update_layout(showlegend=False)
                v2.plotly_chart(bar_fig, use_container_width=True)
                
                # 5. Data Tables (UI)
                t1, t2 = st.tabs(["📊 Category Summary", "💰 Price-wise Category"])
                
                # Prep Summary Table
                df_breakdown = results['summary'].sort_values('Total Qty', ascending=False).copy()
                total_qty = df_breakdown['Total Qty'].sum()
                total_amount = df_breakdown['Total Amount'].sum()
                df_breakdown.loc[len(df_breakdown) + 1] = ['TOTAL SALES (Summary)', total_qty, total_amount]
                df_breakdown.index = range(1, len(df_breakdown) + 1)
                
                # Prep Price-wise Table
                df_drill = results['drilldown'].sort_values(['Category', 'Price'], ascending=[True, False]).copy()
                df_drill.index = range(1, len(df_drill) + 1)

                with t1: 
                    st.dataframe(df_breakdown[['Category', 'Total Qty', 'Total Amount']], use_container_width=True)
                
                with t2: 
                    st.dataframe(df_drill[['Category', 'Price', 'Qty']], use_container_width=True)
                
                # 6. Export functionality (Excel Formatting)
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='xlsxwriter') as wr:
                    # Write sheets
                    df_breakdown.to_excel(wr, sheet_name='Category Summary', index=False)
                    df_drill[['Category', 'Price', 'Qty']].to_excel(wr, sheet_name='Price-wise Category', index=False)
                    results['top_items'].to_excel(wr, sheet_name='Full Product Ranking', index=False)
                    
                    # Access workbook/worksheet objects
                    workbook = wr.book
                    
                    # Formats
                    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
                    currency_format = workbook.add_format({'num_format': '#,##0.00'})
                    num_format = workbook.add_format({'num_format': '#,##0'})
                    
                    for sheet_name in wr.sheets:
                        ws = wr.sheets[sheet_name]
                        # Freeze Panes
                        ws.freeze_panes(1, 0)
                        # Auto-adjust column width (Basic approximation)
                        for i, col in enumerate(df_breakdown.columns if sheet_name == 'Category Summary' else df_drill.columns):
                            ws.set_column(i, i, 20)
                        
                        # Apply specialized formats
                        if sheet_name == 'Category Summary':
                            ws.set_column('B:B', 15, num_format)
                            ws.set_column('C:C', 18, currency_format)
                        elif sheet_name == 'Price-wise Category':
                            ws.set_column('B:B', 15, currency_format)
                            ws.set_column('C:C', 15, num_format)

                fname = f"{mode.replace(' ', '_')}_{results['timeframe']}.xlsx"
                st.download_button("📥 Download Premium Excel Report", data=buf.getvalue(), file_name=fname)
                
        except Exception as e:
            st.error(f"Processing Error: {e}")
            log_event("CRASH", str(e))

    render_footer(logo_b64)

if __name__ == "__main__":
    main()

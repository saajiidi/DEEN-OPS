import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta, timezone
from io import BytesIO
from itertools import combinations

from src.components.snapshot import render_snapshot_button
from src.config.constants import COMMON_CATS
from src.processing.categorization import get_category_for_sales, get_sub_category_for_sales
from src.processing.column_detection import find_columns
from src.processing.data_processing import prepare_granular_data, aggregate_data
from src.processing.forecasting import PredictiveIntelligence
from src.services.woocommerce.client import load_from_woocommerce, get_items_sold_label
from src.utils.product import get_base_product_name, get_size_from_name
from src.utils.snapshots import save_sales_snapshot


@st.cache_data(ttl=3600)
def get_category(name):
    return get_category_for_sales(name)


def render_performance_analysis(df: pd.DataFrame):
    """Generates time-series performance trends for Ingestion analytics."""
    if df.empty or "Date" not in df.columns:
        return

    st.divider()
    c_hdr, c_toggle = st.columns([3, 1])
    with c_hdr:
        st.subheader("\U0001f4c8 Time-Series Performance Analysis")
    with c_toggle:
        enable_ml = st.checkbox("\U0001f680 Enable ML Forecasting", value=False, help="Apply Predictive Intelligence models to forecast future trends.")

    # Pre-processing: Aggregating by Day
    df_day = df.copy()
    # Normalize dates to avoid timestamp artifacts in grouping
    df_day["Day"] = pd.to_datetime(df_day["Date"]).dt.date

    # Daily Revenue & Items Sold
    daily_stats = df_day.groupby("Day").agg({
        "Total Amount": "sum",
        "Quantity": "sum",
        "Order ID": "nunique"
    }).reset_index()

    daily_stats["Avg Basket Value"] = (daily_stats["Total Amount"] / daily_stats["Order ID"]).fillna(0)
    daily_stats = daily_stats.sort_values("Day")

    c1, c2 = st.columns(2)

    with c1:
        # 1. Daily Revenue Trend + ML Forecast
        rev_data = daily_stats.set_index("Day")["Total Amount"]
        fc_res_rev, standings_rev = PredictiveIntelligence.forecast(rev_data) if enable_ml else (None, None)

        fig_rev = px.area(daily_stats, x="Day", y="Total Amount",
                          title=f"Revenue Outlook {'(Best 3 Strategy Ensemble)' if enable_ml else ''}",
                          labels={"Total Amount": "Revenue", "Day": ""},
                          color_discrete_sequence=["#1d4ed8"])

        if enable_ml and fc_res_rev:
            fc_dates = [daily_stats["Day"].iloc[-1] + timedelta(days=i+1) for i in range(7)]
            forecast_colors = ["#4f46e5", "#818cf8", "#c7d2fe"]
            for i, res in enumerate(fc_res_rev):
                fig_rev.add_scatter(x=fc_dates, y=res["forecast"], mode="lines+markers",
                                   name=f"Rank {i+1}: {res['name']}",
                                   line=dict(dash="dot" if i > 0 else "dash", color=forecast_colors[i], width=2 if i == 0 else 1))

        fig_rev.update_layout(margin=dict(l=40, r=20, t=50, b=40), height=350, showlegend=False)
        st.plotly_chart(fig_rev, use_container_width=True, config={"displayModeBar": False})

        # 3. Daily Items Sold Trend + ML Forecast
        qty_data = daily_stats.set_index("Day")["Quantity"]
        fc_res_qty, _ = PredictiveIntelligence.forecast(qty_data) if enable_ml else (None, None)

        fig_qty = px.line(daily_stats, x="Day", y="Quantity",
                          title=f"Volume Outlook {'(Top Models Displayed)' if enable_ml else ''}",
                          labels={"Quantity": "Volume", "Day": ""},
                          color_discrete_sequence=["#10b981"])

        if enable_ml and fc_res_qty:
            fc_dates = [daily_stats["Day"].iloc[-1] + timedelta(days=i+1) for i in range(7)]
            forecast_colors = ["#059669", "#34d399", "#a7f3d0"]
            for i, res in enumerate(fc_res_qty):
                fig_qty.add_scatter(x=fc_dates, y=res["forecast"], mode="lines",
                                   name=f"Rank {i+1}: {res['name']}",
                                   line=dict(dash="dot" if i > 0 else "dash", color=forecast_colors[i], width=2 if i == 0 else 1))

        fig_qty.update_layout(margin=dict(l=40, r=20, t=50, b=40), height=350, showlegend=False)
        st.plotly_chart(fig_qty, use_container_width=True, config={"displayModeBar": False})

    with c2:
        # 2. Daily Order Count Trend + ML Forecast
        ord_data = daily_stats.set_index("Day")["Order ID"]
        fc_res_ord, _ = PredictiveIntelligence.forecast(ord_data) if enable_ml else (None, None)

        fig_ord = px.bar(daily_stats, x="Day", y="Order ID",
                         title=f"Orders Outlook {'(Multi-Model Mode)' if enable_ml else ''}",
                         labels={"Order ID": "Orders", "Day": ""},
                         color_discrete_sequence=["#6366f1"])

        if enable_ml and fc_res_ord:
             fc_dates = [daily_stats["Day"].iloc[-1] + timedelta(days=i+1) for i in range(7)]
             forecast_colors = ["#4f46e5", "#818cf8", "#c7d2fe"]
             for i, res in enumerate(fc_res_ord):
                 fig_ord.add_scatter(x=fc_dates, y=res["forecast"], mode="markers+lines",
                                    name=f"Rank {i+1}: {res['name']}",
                                    line=dict(dash="dot" if i > 0 else "solid", color=forecast_colors[i], width=2 if i == 0 else 1))

        fig_ord.update_layout(margin=dict(l=40, r=20, t=50, b=40), height=350, showlegend=False)
        st.plotly_chart(fig_ord, use_container_width=True, config={"displayModeBar": False})

        # 4. Display Tournament Standing if enabled
        if enable_ml and standings_rev is not None:
             with st.expander("\U0001f3c6 ML Forecasting Tournament Standings"):
                 st.write("**Revenue Performance Leaderboard** (MAE Comparison)")
                 st.dataframe(standings_rev, hide_index=True, use_container_width=True)
                 st.caption("Lower error indicates better historical accuracy for this specific metric.")

        # 4. Daily Basket Value Trend
        fig_bv = px.line(daily_stats, x="Day", y="Avg Basket Value",
                         title="Market Basket Efficiency (AOV)",
                         labels={"Avg Basket Value": "Avg Value", "Day": ""},
                         color_discrete_sequence=["#f59e0b"])
        fig_bv.update_layout(margin=dict(l=40, r=20, t=50, b=40), height=350)
        st.plotly_chart(fig_bv, use_container_width=True, config={"displayModeBar": False})


def render_dashboard_output(
    drill, summ, top, timeframe, basket, source_name, last_updated="N/A", granular_df=None
):
    """Renders common dashboard widgets/charts/tables/export."""

    # Unified Mapping for re-aggregation
    dummy_mapping = {"name":"Product Name", "cost":"Item Cost", "qty":"Quantity", "date":"Date", "order_id":"Order ID", "phone":"Phone", "sku":"SKU"}
    wc_raw_mapping = {"name":"Item Name", "cost":"Item Cost", "qty":"Quantity", "date":"Order Date", "order_id":"Order ID", "phone":"Phone (Billing)", "sku":"SKU"}

    # v13.7 Global Dashboard Container (Ensures snapshot coverage across all modes)
    st.markdown('<div id="snapshot-target-main"></div>', unsafe_allow_html=True)
    render_snapshot_button("snapshot-target-main")

    # v9.6 Unified Metrics Intelligence Engine
    active_df = granular_df

    if st.session_state.get("wc_sync_mode") == "Operational Cycle":
        nav_mode = st.session_state.get("wc_nav_mode", "Today")

        # Select active datasets
        m_df = None
        c_df = None

        if nav_mode == "Prev":
            m_df = st.session_state.get("wc_prev_df")
            c_df = st.session_state.get("wc_curr_df")
        elif nav_mode == "Backlog":
            m_df = st.session_state.get("wc_backlog_df")
        else: # Today
            m_df = st.session_state.get("wc_curr_df")
            c_df = st.session_state.get("wc_prev_df")

        if m_df is not None:
            # v10.1 Resiliency: Ensure both active and comparison dataframes are standardized
            if "Category" not in m_df.columns or "Product Name" not in m_df.columns or "Clean_Product" not in m_df.columns:
                m_df, _ = prepare_granular_data(m_df, wc_raw_mapping)
            if c_df is not None and ("Category" not in c_df.columns or "Product Name" not in c_df.columns or "Clean_Product" not in c_df.columns):
                c_df, _ = prepare_granular_data(c_df, wc_raw_mapping)

            # v14.2: Update active_df AFTER standardization to ensure all columns (Clean_Product) exist
            active_df = m_df

            # Re-calculate EVERYTHING from m_df (Filters removed from Live Dashboard as requested)
            drill, summ, top, basket = aggregate_data(m_df, dummy_mapping)

            # Metrics Calculation
            m_qty = m_df["Quantity"].sum()
            m_rev = (m_df["Quantity"] * m_df["Item Cost"]).sum()
            m_ord = basket["total_orders"]
            m_bv = basket["avg_basket_value"]

            # Status Drilldown
            is_ship = m_df["Order Status"].isin(["completed", "shipped", "confirmed"])
            is_proc = m_df["Order Status"] == "processing"
            is_hold = m_df["Order Status"] == "on-hold"
            is_wait = m_df["Order Status"] == "pending"

            ship_count = m_df[is_ship]["Order ID"].nunique()
            proc_count = m_df[is_proc]["Order ID"].nunique()
            hold_count = m_df[is_hold]["Order ID"].nunique()
            wait_count = m_df[is_wait]["Order ID"].nunique()

            # v11.5 Confirmed Status tracking
            is_conf = m_df["Order Status"] == "confirmed"
            conf_count = m_df[is_conf]["Order ID"].nunique()

            # Comparison Metrics
            dq_str, dr_str, do_str, db_str = None, None, None, None
            if c_df is not None and not c_df.empty:
                co_q = c_df["Quantity"].sum()
                co_r = (c_df["Quantity"] * c_df["Item Cost"]).sum()
                # Re-calculate comparison basket
                _, _, _, co_basket = aggregate_data(c_df, dummy_mapping)
                co_o = co_basket["total_orders"]
                co_b = co_basket["avg_basket_value"]

                prefix = "Today " if nav_mode == "Prev" else ""
                suffix = "" if nav_mode == "Prev" else " vs Prev"

                dq, dr, d_o, db = (m_qty-co_q), (m_rev-co_r), (m_ord-co_o), (m_bv-co_b)
                if nav_mode == "Prev": # Compare Yesterday to Today (invert for benchmarking)
                    dq, dr, d_o, db = (co_q-m_qty), (co_r-m_rev), (co_o-m_ord), (co_b-m_bv)

                dq_str = f"{prefix}{dq:+,.0f}{suffix}"
                dr_str = f"{prefix}{'+' if dr >= 0 else '-'}TK {abs(dr):,.0f}{suffix}"
                do_str = f"{prefix}{d_o:+,.0f}{suffix}"
                db_str = f"{prefix}{'+' if db >= 0 else '-'}TK {abs(db):,.0f}{suffix}"

            # Render Headers
            curr_s, curr_e = st.session_state.wc_curr_slot
            prev_s, prev_e = st.session_state.wc_prev_slot
            now_bd = datetime.now(timezone(timedelta(hours=6)))
            now_mins = now_bd.hour * 60 + now_bd.minute
            is_office_hours = 570 <= now_mins < 1050

            # Header removed per user request
            sync_label = "Just now"
            if st.session_state.get("live_sync_time"):
                diff = datetime.now() - st.session_state.live_sync_time
                mins = int(diff.total_seconds() / 60)
                sync_label = "Just now" if mins < 1 else f"{mins}m ago"

            # Intelligence Layer Integration (Panel removed per user request)
            # insights = get_business_insights(m_df)
            # render_insight_panel(insights)

            # v11.0 UI Cleanup: Only show Operation Mode in Live Dashboard
            if st.session_state.get("wc_sync_mode") == "Operational Cycle":
                nav_mode = st.session_state.get("wc_nav_mode", "Today")
                st.markdown('<div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; color: #475569;">Operation Mode</div>', unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns([1, 1.2, 1, 2.5])
                with c1:
                    if st.button("\U0001f552 History", type="primary" if nav_mode == "Prev" else "secondary", use_container_width=True):
                        st.session_state.wc_nav_mode = "Prev"; st.rerun()
                with c2:
                    if st.button(f"\U0001f3af Active ({sync_label})", type="primary" if nav_mode == "Today" else "secondary", use_container_width=True):
                        st.session_state.wc_nav_mode = "Today"; st.rerun()
                with c3:
                    if st.button("\U0001f4e5 Queue", type="primary" if nav_mode == "Backlog" else "secondary", use_container_width=True):
                        st.session_state.wc_nav_mode = "Backlog"; st.rerun()

            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    l1 = "Backlog Items" if nav_mode == "Backlog" else "Gross Sales Items"
                    st.metric(l1, f"{m_qty:,.0f}", delta=dq_str, help="Includes Shipped, Confirmed, and Completed orders.")
                with col2:
                    l2 = "Backlog Rev" if nav_mode == "Backlog" else "Revenue"
                    st.metric(l2, f"TK {m_rev:,.0f}", delta=dr_str)
                with col3:
                    l3 = "Backlog Orders" if nav_mode == "Backlog" else "Orders"
                    st.metric(l3, f"{m_ord:,.0f}", delta=do_str)
                with col4:
                    st.metric("Avg Basket", f"TK {m_bv:,.0f}", delta=db_str)
            st.divider()

    else:
        # v11.4 High-Density Intelligence: Acquisition and Filtering in a single horizontal bar
        is_manual = st.session_state.get("manual_tab_active", False)

        if granular_df is not None or is_manual:
             with st.expander("\U0001f6e0\ufe0f Filter Intelligence", expanded=True):
                # Predefined logic for high-density bar
                _COMMON_CATS = COMMON_CATS

                # Setup Data Containers
                working_df = granular_df.copy() if granular_df is not None else pd.DataFrame(columns=["Category", "Product Name", "Size", "Date"])
                if not working_df.empty:
                     if "Category" not in working_df.columns or "Sub-Category" not in working_df.columns or "Clean_Product" not in working_df.columns:
                         working_df, _ = prepare_granular_data(working_df, dummy_mapping)

                # High-Density Bar Columns
                c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 0.3])

                with c1:
                    last_range = st.session_state.get("last_synced_range")
                    sel_range = st.date_input(
                        "Select Date Range",
                        value=st.session_state.get("ingest_range", ((datetime.now() - timedelta(days=7)).date(), datetime.now().date())),
                        min_value=datetime(2021, 8, 31).date(),
                        max_value=datetime.now().date(),
                        key="ingest_range"
                    )

                    # AUTO-FETCH LOGIC
                    if isinstance(sel_range, tuple) and len(sel_range) == 2:
                        # Try to detect change to trigger auto-sync
                        if sel_range != last_range:
                            st.session_state["last_synced_range"] = sel_range
                            s_d, e_d = sel_range

                            # Update global sync params
                            st.session_state["wc_sync_mode"] = "Custom Range"
                            st.session_state["wc_sync_start_date"] = s_d
                            st.session_state["wc_sync_start_time"] = datetime.strptime("00:00", "%H:%M").time()
                            st.session_state["wc_sync_end_date"] = e_d
                            st.session_state["wc_sync_end_time"] = datetime.strptime("23:59", "%H:%M").time()

                            # Use a temporary spinner to fetch
                            with st.spinner(f"\U0001f680 Syncing {s_d} to {e_d}..."):
                                try:
                                    wc_res = load_from_woocommerce()
                                    df_res = wc_res["df_to_return"]
                                    if not df_res.empty:
                                        st.session_state.manual_df = df_res
                                        st.session_state.manual_source_name = wc_res["sync_desc"]
                                        save_sales_snapshot(df_res)
                                        st.toast("\u2705 Auto-Sync Complete!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Auto-sync failed: {e}")

                    # v11.4: Sync view with Acquisition Range immediately for local filtering
                    if not working_df.empty and isinstance(sel_range, tuple) and len(sel_range) == 2:
                         sd, ed = pd.to_datetime(sel_range[0]), pd.to_datetime(sel_range[1])
                         working_df = working_df[(working_df["Date"] >= sd) & (working_df["Date"] <= (ed + timedelta(days=1)))]

                # Assign to active context for later visualizations
                active_df = working_df

                with c2:
                    # v11.8 Unified Hierarchical Filter
                    unified_options = []
                    if not working_df.empty:
                        for cat in sorted(working_df["Category"].unique().tolist()):
                            unified_options.append(cat)
                            subs = sorted(working_df[working_df["Category"] == cat]["Sub-Category"].unique().tolist())
                            for s in subs:
                                if s not in ["All", "N/A", cat]:
                                    unified_options.append(f"  \u21b3 {s}")
                    else:
                        unified_options = sorted(_COMMON_CATS)

                    sel_unified = st.multiselect("Select Category / Fit", unified_options, placeholder="All Categories", key="fallback_filter_unified")

                    if not working_df.empty and sel_unified:
                        from pandas import Index
                        mask = pd.Series(False, index=working_df.index)
                        for opt in sel_unified:
                            if "  \u21b3 " in opt:
                                sub_name = opt.replace("  \u21b3 ", "")
                                mask |= (working_df["Sub-Category"] == sub_name)
                            else:
                                mask |= (working_df["Category"] == opt)
                        working_df = working_df[mask]

                with c3:
                    # v11.4: Use Filter_Identity (Name + SKU) without size redundancy
                    all_prods = sorted(working_df["Filter_Identity"].unique().tolist()) if not working_df.empty else []
                    sel_prods = st.multiselect("Select Item", all_prods, placeholder="All Products", key="fallback_filter_prod")
                    if not working_df.empty:
                        working_df = working_df[working_df["Filter_Identity"].isin(sel_prods)] if sel_prods else working_df

                with c4:
                    all_sizes = sorted(working_df["Size"].unique().tolist()) if not working_df.empty and "Size" in working_df.columns else []
                    sel_sizes = st.multiselect("Select Size", all_sizes, placeholder="All Sizes", key="fallback_filter_size")
                    if not working_df.empty and "Size" in working_df.columns:
                        working_df = working_df[working_df["Size"].isin(sel_sizes)] if sel_sizes else working_df

                with c5:
                    st.markdown('<div style="height: 28px;"></div>', unsafe_allow_html=True)
                    if st.button("\U0001f504", use_container_width=True, type="primary", help="Sync Fresh Data"):
                         if isinstance(sel_range, tuple) and len(sel_range) == 2:
                            s_d, e_d = sel_range
                            st.session_state["wc_sync_mode"] = "Custom Range"
                            st.session_state["wc_sync_start_date"] = s_d
                            st.session_state["wc_sync_start_time"] = datetime.strptime("00:00", "%H:%M").time()
                            st.session_state["wc_sync_end_date"] = e_d
                            st.session_state["wc_sync_end_time"] = datetime.strptime("23:59", "%H:%M").time()

                            try:
                                with st.spinner("\U0001f504 Fetching..."):
                                    wc_res = load_from_woocommerce()
                                    df_res = wc_res["df_to_return"]
                                    if not df_res.empty:
                                        # Apply Multiselect Filters immediately to the fetch results
                                        # v11.8 Unified Filtering Logic for Sync
                                        if sel_unified:
                                            df_res["_TmpCat"] = df_res["Item Name"].apply(get_category)
                                            df_res["_TmpSub"] = df_res.apply(lambda r: get_sub_category_for_sales(r["Item Name"], r["_TmpCat"]), axis=1)

                                            mask = pd.Series(False, index=df_res.index)
                                            for opt in sel_unified:
                                                if "  \u21b3 " in opt:
                                                    sub_name = opt.replace("  \u21b3 ", "")
                                                    mask |= (df_res["_TmpSub"] == sub_name)
                                                else:
                                                    mask |= (df_res["_TmpCat"] == opt)

                                            df_res = df_res[mask]
                                            if "_TmpCat" in df_res.columns: df_res = df_res.drop(columns=["_TmpCat"])
                                            if "_TmpSub" in df_res.columns: df_res = df_res.drop(columns=["_TmpSub"])

                                        if sel_prods:
                                            df_res["_TmpIdent"] = df_res.apply(lambda r: f"{get_base_product_name(r['Item Name'])} [{r['SKU']}]", axis=1)
                                            df_res = df_res[df_res["_TmpIdent"].isin(sel_prods)].drop(columns=["_TmpIdent"])
                                        if sel_sizes:
                                            df_res["_TmpSize"] = df_res["Item Name"].apply(get_size_from_name)
                                            df_res = df_res[df_res["_TmpSize"].isin(sel_sizes)].drop(columns=["_TmpSize"])
                                        if not df_res.empty:
                                            st.session_state.manual_df = df_res
                                            st.session_state.manual_source_name = wc_res["sync_desc"]
                                            save_sales_snapshot(df_res)
                                            st.toast("\u2705 API Sync Complete!")
                                            st.rerun()
                                        else:
                                            st.warning("No data found for the selected Category/Item/Size combination.")
                                    else:
                                        st.warning("No data found for the selected range.")
                            except Exception as e:
                                st.error(f"Ingestion failed: {e}")
                         else:
                            st.error("Please select both a start and end date.")

                # v14.2: Sync active_df for intelligence and re-aggregate visuals
                active_df = working_df
                if not working_df.empty:
                    drill, summ, top, basket = aggregate_data(working_df, dummy_mapping)
                else:
                    drill, summ, top, basket = None, None, None, None

        if granular_df is not None and summ is not None:
             with st.container():
                st.markdown('<div id="snapshot-target-main"></div>', unsafe_allow_html=True)
                st.subheader("Core Metrics")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(get_items_sold_label(last_updated), f"{summ['Total Qty'].sum():,.0f}")
                total_orders = basket.get("total_orders", 0) if basket else 0
                m2.metric("Number of Orders", f"{total_orders:,.0f}" if total_orders else "-")
                m3.metric("Revenue", f"TK {summ['Total Amount'].sum():,.0f}")
                avg_b = basket.get('avg_basket_value', 0) if basket else 0
                m4.metric("Market Basket Value", f"TK {avg_b:,.0f}")
                st.divider()


    st.subheader("Performance Outlook")
    # ... rest of visuals continue using 'summ', 'top', 'drill' which are now filtered ...
    # v14.0 selection Intelligence: Display Sub-Category if specifically filtered
    sel_unified = st.session_state.get("fallback_filter_unified", [])
    is_sub_filtering = any("  \u21b3 " in opt for opt in sel_unified) if sel_unified else False

    display_col = "Category"
    if "Sub-Category" in summ.columns:
        # v14.9: Simplify to ONLY sub-category name as requested for cleaner readability
        display_col = "Sub-Category"

    sorted_cats = summ.sort_values("Total Amount", ascending=False)[display_col].tolist()
    color_map = {cat: px.colors.sample_colorscale("Plasma", [(i/max(1, len(sorted_cats)-1))*0.85 if len(sorted_cats)>1 else 0])[0] for i, cat in enumerate(sorted_cats)}

    v1, v2 = st.columns(2)
    with v1:
        fig_pie = px.pie(summ, values="Total Amount", names=display_col, color=display_col, hole=0.6, title="Revenue Share (TK)", color_discrete_map=color_map)
        fig_pie.update_layout(margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        fig_pie.update_traces(textposition="inside", textinfo="label+percent", textfont_size=11)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with v2:
        # v14.8: Enforce consistent coloring using display_col for unique item identification
        bar_axis = "Sub-Category" if "Sub-Category" in summ.columns else display_col
        sorted_bars = summ.sort_values("Total Qty", ascending=False)[bar_axis].tolist()
        fig_bar = px.bar(
            summ.sort_values("Total Qty", ascending=False),
            x=bar_axis, y="Total Qty", color=display_col,
            title="Volume by Fit/Type Breakdown", text_auto=".0f",
            color_discrete_map=color_map,
            category_orders={bar_axis: sorted_bars}
        )
        fig_bar.update_layout(margin=dict(l=50, r=10, t=50, b=40), xaxis_title="", yaxis_title="Quantity Sold", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    if top is not None:
        st.subheader("\U0001f525 Products Spotlight")
        sc1, sc2 = st.columns([1, 1])
        with sc1:
            strategy = st.selectbox("Spotlight Strategy", ["Top 10", "Top 20", "Underperformers", "Custom Range"], key="spotlight_strat")

        limit = 10
        ascending = False
        if strategy == "Top 10": limit = 10
        elif strategy == "Top 20": limit = 20
        elif strategy == "Underperformers": limit = 10; ascending = True

        if strategy == "Custom Range" and not top.empty:
            with sc2:
                c_range = st.slider("Select Rank Range", 1, len(top), (1, min(10, len(top))))
                spotlight = top.iloc[c_range[0]-1 : c_range[1]].sort_values("Total Amount", ascending=True)
        else:
            spotlight = top.sort_values("Total Amount", ascending=not ascending).head(limit).sort_values("Total Amount", ascending=True)

        # v14.3: Add SKU to Label and enrich hover data
        spotlight["Display_Name"] = spotlight.apply(lambda r: f"{r['Product Name']} [{r['SKU']}]", axis=1)
        spotlight["Label"] = spotlight["Display_Name"]

        if not ascending:
            top_indices = spotlight.tail(3).index if len(spotlight) >= 3 else spotlight.index
            spotlight.loc[top_indices, "Label"] = "\U0001f525 " + spotlight.loc[top_indices, "Display_Name"]
        else:
            bot_indices = spotlight.head(3).index if len(spotlight) >= 3 else spotlight.index
            spotlight.loc[bot_indices, "Label"] = "\u26a0\ufe0f " + spotlight.loc[bot_indices, "Display_Name"]

        fig_top = px.bar(
            spotlight, x="Total Amount", y="Label", orientation="h", color="Category",
            title=f"Spotlight: {strategy}", text_auto=".2s", color_discrete_map=color_map,
            hover_data={
                "Label": False,
                "Product Name": True,
                "SKU": True,
                "Sub-Category": True,
                "Total Qty": ":.0f",
                "Total Amount": ":,.0f"
            }
        )
        fig_top.update_layout(margin=dict(l=12, r=12, t=50, b=12), yaxis_title="", xaxis_title="Revenue (TK)", showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})


    st.subheader("Deep Dive Data")
    tabs = st.tabs(["Summary", "Rankings", "Drilldown"])
    with tabs[0]: st.dataframe(summ.sort_values("Total Amount", ascending=False), use_container_width=True, hide_index=True)
    with tabs[1]: st.dataframe(top.sort_values("Total Amount", ascending=False).head(20), use_container_width=True, hide_index=True)
    with tabs[2]: st.dataframe(drill.sort_values("Total Amount", ascending=False), use_container_width=True, hide_index=True)

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as wr:
        summ.to_excel(wr, sheet_name="Summary", index=False)
        top.to_excel(wr, sheet_name="Rankings", index=False)
        drill.to_excel(wr, sheet_name="Details", index=False)

    base_name = os.path.splitext(os.path.basename(source_name))[0]
    st.download_button("Export filtered Report", data=buf.getvalue(), file_name=f"Report_{base_name}.xlsx")

    # v13.7: Relocated Intelligence Sections
    st.divider()
    # 1. Market Basket Intelligence
    st.subheader("\U0001f916 Intelligence: Market Basket & Association Rules")
    with st.expander("Explore Association Rules (Support / Confidence / Lift)", expanded=True):
        st.info("\U0001f4a1 **Machine Learning Insight**: Association Rule Learning finds 'If-Then' rules in your data (e.g., 'If they buy Hoodies, they buy Pants 80% of the time').")
        if active_df is not None and not active_df.empty:
            order_col = "Order ID" if "Order ID" in active_df.columns else "Order Number"
            if order_col in active_df.columns:
                basket_df = active_df.groupby(order_col)["Clean_Product"].apply(list).reset_index()
                basket_df = basket_df[basket_df["Clean_Product"].apply(len) > 1]
                if not basket_df.empty:
                    all_combinations = []
                    for products in basket_df["Clean_Product"]:
                        all_combinations.extend(list(combinations(set(products), 2)))
                    if all_combinations:
                        pairs_df = pd.DataFrame(all_combinations, columns=["Product A", "Product B"])
                        combo_counts = pairs_df.value_counts().reset_index(name="Frequency")
                        combo_counts = combo_counts.sort_values("Frequency", ascending=False)
                        total_orders_ref = basket.get("total_orders", 1) if basket else (basket_df[order_col].nunique() if not basket_df.empty else 1)
                        combo_counts["Support (%)"] = (combo_counts["Frequency"] / total_orders_ref * 100).round(2)
                        # BUG FIX #7: Calculate actual Confidence and Lift from frequency data
                        product_freq = {}
                        for products in basket_df["Clean_Product"]:
                            for p in set(products):
                                product_freq[p] = product_freq.get(p, 0) + 1
                        total_baskets = len(basket_df)
                        combo_counts["Confidence (%)"] = combo_counts.apply(
                            lambda r: round(r["Frequency"] / max(product_freq.get(r["Product A"], 1), 1) * 100, 2), axis=1
                        )
                        combo_counts["Lift Index"] = combo_counts.apply(
                            lambda r: round(
                                (r["Frequency"] / total_baskets) /
                                max((product_freq.get(r["Product A"], 1) / total_baskets) * (product_freq.get(r["Product B"], 1) / total_baskets), 0.001),
                                2
                            ), axis=1
                        )
                        st.write("\U0001f527 **Top Bundle Affinities**: Optimized for Cross-Sell & Up-Sell Strategy")
                        st.dataframe(combo_counts.head(10), use_container_width=True, hide_index=True)
                        st.caption("Attachment Rate: The percentage of orders with complementary items.")
                else:
                    st.write("No significant bundle behaviors identified in this range.")

    # 2. Daily Performance Trend
    if active_df is not None and "Date" in active_df.columns:
         render_performance_analysis(active_df)

    st.divider()

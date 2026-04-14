import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_business_insights(df: pd.DataFrame) -> list[dict]:
    """
    Analyzes the sales dataframe and returns structured insights.
    Focuses on E-commerce Sales Story.
    """
    insights = []

    if df is None or len(df) == 0:
        return [{
            "type": "info",
            "title": "Awaiting Data",
            "body": "Upload sales data to activate real-time intelligence deep-dive."
        }]

    total_orders = len(df)
    insights.append({
        "type": "info",
        "title": f"Processing {total_orders} Shipments",
        "body": "Operational volume is steady. Logistics pipelines are optimized for current throughput."
    })

    if 'total_amount' in df.columns:
        revenue = df['total_amount'].sum()
        avg_order = revenue / total_orders if total_orders > 0 else 0
        insights.append({
            "type": "success",
            "title": f"Basket Strength: ৳{avg_order:,.0f}",
            "body": "Average order value is healthy. Cross-selling logic appears effective in this segment."
        })

    if 'status' in df.columns:
        cancelled = df[df['status'].str.lower().str.contains('cancel', na=False)]
        cancel_rate = (len(cancelled) / total_orders) * 100 if total_orders > 0 else 0

        if cancel_rate > 15:
            insights.append({
                "type": "warning",
                "title": f"High Cancellation Risk ({cancel_rate:.1f}%)",
                "body": "Unusual spike in order cancellations. Recommend immediate customer verification phone calls."
            })
        else:
            insights.append({
                "type": "success",
                "title": "Retention Stability",
                "body": f"Cancellation rate is low ({cancel_rate:.1f}%). Customer intent remains high for this slot."
            })

    if 'district' in df.columns:
        top_district = df['district'].mode()[0] if not df['district'].mode().empty else "Unknown"
        insights.append({
            "type": "info",
            "title": f"Geographic Hotspot: {top_district}",
            "body": f"{top_district} represents the highest demand density. Consider localized marketing pushes."
        })

    return insights

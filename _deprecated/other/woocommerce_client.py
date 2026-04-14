# woocommerce_client.py - API interface for fetching sales and stock data
from woocommerce import API
import pandas as pd
from datetime import datetime

def get_wc_api(url, ck, cs):
    """Initializes and returns WooCommerce API client."""
    return API(
        url=url,
        consumer_key=ck,
        consumer_secret=cs,
        version="wc/v3",
        timeout=30
    )

def fetch_wc_orders(wcapi, filter_type="Date Range", **kwargs):
    """Fetches orders based on various filters (Date, Last X Shipped, Order ID Range)."""
    params = {"per_page": 100, "status": "any", "orderby": "date", "order": "desc"}
    
    if filter_type == "Date Range":
        params["after"] = f"{kwargs.get('start_date')}T00:00:00"
        params["before"] = f"{kwargs.get('end_date')}T23:59:59"
    elif filter_type == "Last Shipped Orders":
        params["status"] = "shipped"
        params["per_page"] = kwargs.get("limit", 25)
    
    orders = []
    page = 1
    while True:
        res = wcapi.get("orders", params={**params, "page": page})
        if res.status_code != 200: break
        batch = res.json()
        if not batch: break
        orders.extend(batch)
        if filter_type == "Last Shipped Orders": break # Limit handled by per_page
        page += 1
    
    rows = []
    for order in orders:
        o_id = order.get('id')
        
        # Order ID Filter logic (client-side for range)
        if filter_type == "Order No. Range":
            min_id = kwargs.get('min_id', 0)
            max_id = kwargs.get('max_id', 999999)
            if not (min_id <= o_id <= max_id):
                continue

        date = order.get('date_created')
        phone = order.get('billing', {}).get('phone')
        for item in order.get('line_items', []):
            rows.append({
                'Order ID': o_id,
                'Order Date': date,
                'Customer Phone': phone,
                'Product Name': item.get('name'),
                'Price': item.get('price'),
                'Quantity': item.get('quantity')
            })
    return pd.DataFrame(rows)

def fetch_wc_products(wcapi):
    """Fetches all products and their variations for stock count."""
    products = []
    page = 1
    while True:
        res = wcapi.get("products", params={"per_page": 100, "page": page})
        if res.status_code != 200: break
        batch = res.json()
        if not batch: break
        products.extend(batch)
        page += 1
    
    rows = []
    for p in products:
        p_name = p.get('name')
        # If it's a variable product, we'll need to fetch variations
        if p.get('type') == 'variable':
            # Note: Fetching variations for EACH product is costly. 
            # In a production app, we'd use more optimal batch calls.
            v_res = wcapi.get(f"products/{p.get('id')}/variations", params={"per_page": 100})
            if v_res.status_code == 200:
                for v in v_res.json():
                    rows.append({
                        'Product Name': f"{p_name} - {', '.join([attr.get('option') for attr in v.get('attributes', [])])}",
                        'Price': v.get('price') or v.get('regular_price'),
                        'Quantity': v.get('stock_quantity') or 0
                    })
        else:
            rows.append({
                'Product Name': p_name,
                'Price': p.get('price') or p.get('regular_price'),
                'Quantity': p.get('stock_quantity') or 0
            })
    return pd.DataFrame(rows)

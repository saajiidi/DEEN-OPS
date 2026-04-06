# DEEN Business Intelligence v9.5

**DEEN Business Intelligence** is a high-performance, intelligence-driven command center for sales analysis, order processing, and real-time inventory management.

## Main Navigation

- **📈 Live Dashboard**: Operations-focused command center with shift-monitoring (Today vs Prev Slot).
- **📥 Sales Data Ingestion**: Manual sales file upload and deep-dive analytics.
- **📦 Current Stock Analytics**: Category-mapped inventory intelligence synced directly from WooCommerce.
- **📋 Bulk Order Processor**: High-volume courier order repair and formatting.
- **📊 Inventory Distribution**: Consolidated stock analyzer and distribution management.
- **💬 WhatsApp Messaging**: Live-synced messaging system for customer verification.

## Key Updates in v9.5

- **Shift-Category Stock Mapping**: Integrated expert rules to group all live warehouse stock into 28 operational categories.
- **Unified Command Center**: High-density operational row featuring Revenue, Orders, and Basket Value with Today-centric deltas.
- **Cross-Slot Intelligence**: Bidirectional time travel between "Today" and "Previous Slot" for instant performance benchmarking.
- **Premium Aesthetics**: Dark-mode optimized, high-density UI with real-time dynamic clocks.

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

- `app.py`: Application shell, sidebar settings, and navigation.
- `app_modules/sales_dashboard.py`: Core logic for live/manual sales analytics.
- `app_modules/pathao_tab.py`: Optimized bulk order processing.
- `app_modules/fuzzy_parser_tab.py`: Advanced text-to-data extraction.
- `app_modules/distribution_tab.py`: Inventory and distribution management.
- `app_modules/wp_tab.py`: WhatsApp link generation and live integration.
- `app_modules/persistence.py`: Session state saving and file handling.

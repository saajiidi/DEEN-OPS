# Migration Log

## Overview

Full restructuring from flat `app_modules/` layout to modular `src/` package architecture.
All features preserved. All session state keys unchanged.

## Directory Changes

| Old Location | New Location |
|-------------|-------------|
| `app_modules/sales_dashboard.py` | Split into 12+ files across `src/` (see below) |
| `app_modules/utils.py` | `src/utils/text.py`, `src/utils/product.py`, `src/processing/categorization.py` |
| `app_modules/ui_components.py` | `src/components/styles.py`, `header.py`, `footer.py`, `sidebar.py`, `widgets.py` |
| `app_modules/ui_config.py` | `src/config/ui_config.py` |
| `app_modules/processor.py` | `src/processing/order_processor.py` |
| `app_modules/wp_processor.py` | `src/processing/whatsapp_processor.py` |
| `app_modules/wp_tab.py` | `src/pages/whatsapp_messaging.py` |
| `app_modules/pathao_tab.py` | `src/pages/pathao_orders.py` |
| `app_modules/pathao_client.py` | `src/services/pathao/client.py` |
| `app_modules/distribution_tab.py` | `src/pages/inventory_distribution.py` |
| `app_modules/fuzzy_parser_tab.py` | `src/pages/delivery_parser.py` + `src/processing/delivery_parser.py` |
| `app_modules/ai_pilot.py` | `src/pages/data_pilot.py` |
| `app_modules/llm_manager.py` | `src/services/llm/manager.py` |
| `app_modules/persistence.py` | `src/state/persistence.py` |
| `app_modules/error_handler.py` | `src/utils/logging.py` (merged with log_system_event) |
| `app_modules/insights_service.py` | `src/state/insights.py` |
| `app_modules/clock.py` | `src/components/clock.py` |
| `app_modules/bike_animation.py` | `src/components/bike_animation.py` |
| `inventory_modules/core.py` | `src/inventory/core.py` |
| `other/` | `_deprecated/` |

## sales_dashboard.py Decomposition (2,190 lines)

The monolithic file was split into:

| Function/Section | Destination |
|-----------------|-------------|
| `get_setting()`, `get_gcp_service_account_info()` | `src/config/settings.py` |
| `DATA_DIR`, `FEEDBACK_DIR`, path constants | `src/config/constants.py` |
| `log_system_event()` | `src/utils/logging.py` |
| `read_sales_file()`, `to_excel_bytes()` | `src/utils/file_io.py` |
| `load/save_stock_snapshot()`, `load/save_sales_snapshot()` | `src/utils/snapshots.py` |
| `find_columns()`, `scrub_raw_dataframe()` | `src/processing/column_detection.py` |
| `process_data()`, `prepare_granular_data()`, `aggregate_data()` | `src/processing/data_processing.py` |
| `PredictiveIntelligence` class | `src/processing/forecasting.py` |
| `load_from_woocommerce()`, `load_live_source()` | `src/services/woocommerce/client.py` |
| `fetch_woocommerce_stock()` | `src/services/woocommerce/stock.py` |
| `render_dashboard_output()`, `render_performance_analysis()` | `src/pages/dashboard_output.py` |
| `render_live_tab()` (Live Dashboard) | `src/pages/live_dashboard.py` |
| `render_manual_tab()` (Sales Ingestion) | `src/pages/sales_ingestion.py` |
| `render_stock_analytics_tab()` | `src/pages/stock_analytics.py` |

## Bugs Fixed

| # | Description | Location |
|---|------------|----------|
| 1 | Duplicate `get_size_from_name` with `@lru_cache` shadowing import from utils | Removed duplicate; using single definition in `src/utils/product.py` |
| 2 | Orphaned unreachable `return "Others"` after function body | Removed |
| 3 | `raw_qty` undefined in stock analytics recovery mode | Replaced with `total_qty` |
| 4 | Unused `email.utils.parsedate_to_datetime` import | Removed |
| 5 | Unused `urllib.request` and `urllib.parse` imports | Removed |
| 6 | `save_user_feedback()` defined but never called | Removed |
| 7 | Association Rules Confidence/Lift using `np.random.rand()` (fake values) | Replaced with actual calculations from co-occurrence data |
| 8 | `show_last_updated()` in ui_components.py never called | Removed |

## Dead Code Removed

- `save_user_feedback()` function
- Duplicate `get_size_from_name()` definition
- Orphaned `return "Others"` statement
- Unused imports: `email.utils`, `urllib.request`, `urllib.parse`
- `show_last_updated()` function
- Commented-out insight panel calls
- Legacy `other/` directory moved to `_deprecated/`

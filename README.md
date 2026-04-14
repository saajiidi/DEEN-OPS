# DEEN OPS Terminal

### AI-Powered Operational Command Center for E-Commerce

> "Most dashboards show data. This one explains it."

DEEN OPS Terminal is a high-performance, intelligence-driven command center designed to optimize E-commerce operations through real-time data storytelling and AI-assisted decision making.

---

## Tech Stack

- **Frontend**: Streamlit + Custom CSS (Glassmorphism & Radial Gradients)
- **Data Engine**: Vectorized Pandas operations, Plotly charting
- **AI Layer**: Multi-provider LLM wrapper (OpenRouter, Gemini, Groq, Ollama) with failover
- **Integrations**: WooCommerce REST API, Pathao Courier API, Google Sheets
- **Reliability**: Error logging, session persistence, multi-threaded API fetching

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Install & Run

```bash
git clone https://github.com/saajiidi/DEEN-BI.git
cd dashboard_v1
pip install -r requirements.txt
streamlit run app.py
```

### Configuration

Copy `.env.example` and configure your secrets:

```bash
cp .env.example .streamlit/secrets.toml
```

Required secrets in `.streamlit/secrets.toml`:

```toml
[woocommerce]
url = "https://your-store.com"
consumer_key = "ck_..."
consumer_secret = "cs_..."

[pathao]
base_url = "https://courier-api.pathao.com"
client_id = "..."
client_secret = "..."
username = "..."
password = "..."

[llm]
openrouter_key = "..."
gemini_key = "..."
groq_key = "..."

# Optional: Google OIDC auth
[auth]
redirect_uri = "..."
cookie_secret = "..."

[auth.google]
client_id = "..."
client_secret = "..."
server_metadata_url = "..."
```

## Workspaces

| Workspace | Description |
|-----------|-------------|
| Live Dashboard | Real-time WooCommerce sync with KPI cards, trend analysis, and ML forecasting |
| Sales Data Ingestion | Upload/fetch sales data with auto-categorization and aggregation |
| Current Stock Analytics | WooCommerce stock monitoring with bundle intelligence |
| Bulk Order Processer | Pathao courier integration for bulk order preparation |
| Inventory Distribution | Multi-location inventory matrix with fulfillment suggestions |
| WhatsApp Messaging | Order-to-WhatsApp message generator with gender-aware salutations |
| Delivery Data Parser | Fuzzy parsing of unstructured delivery records |
| Data Pilot | Conversational AI agent for dataset analysis |

## Project Structure

```
dashboard_v1/
├── app.py                    # Entry point: auth, routing, layout
├── requirements.txt
├── .streamlit/secrets.toml   # API keys & config (not committed)
├── assets/                   # Images, logos
├── resources/                # Static data (Pathao city/zone maps)
├── data/                     # Runtime data directory
│
├── src/
│   ├── config/               # Settings, UI config, path constants
│   ├── services/             # External API clients
│   │   ├── woocommerce/      # WooCommerce client & stock fetcher
│   │   ├── pathao/           # Pathao courier API client
│   │   ├── llm/              # Multi-provider LLM manager
│   │   └── google/           # Google Sheets loader
│   ├── processing/           # Data transformation pipeline
│   ├── inventory/            # Inventory matching engine
│   ├── components/           # Reusable UI components
│   ├── pages/                # One file per workspace tab
│   ├── utils/                # Text, product, file I/O, logging helpers
│   └── state/                # Session persistence & insights
│
├── tests/                    # pytest test suite
├── scripts/                  # Standalone utility scripts
└── _deprecated/              # Legacy code (archived)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed data flow and module responsibilities.
See [DEVELOPMENT.md](DEVELOPMENT.md) for development workflow.

## Testing

```bash
pip install -r requirements_dev.txt
pytest tests/ -v
```

## Author

**Sajid Islam**
*Data Product Engineer specializing in AI-Driven Operational Tools.*

[LinkedIn](https://www.linkedin.com/in/sajidislam/) | [Portfolio](https://saajiidi.github.io/) | [DEEN Commerce](https://deencommerce.com/)

---
*DEEN Commerce Ltd.*

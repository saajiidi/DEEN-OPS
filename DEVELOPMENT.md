# Development Guide

## Setup

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install dev dependencies (testing, linting)
pip install -r requirements_dev.txt

# Run the app
streamlit run app.py
```

## Adding a New Workspace Page

1. Create `src/pages/your_page.py` with a `render_your_tab()` function
2. Add the nav label to `PRIMARY_NAV` in `src/config/ui_config.py`
3. Add the routing case in `app.py` under the `selected_nav` conditionals
4. Register a reset function if the page uses session state (see existing pages for pattern)

## Adding a New Service Integration

1. Create a module under `src/services/your_service/`
2. Add API credentials to `.streamlit/secrets.toml`
3. Load config via `st.secrets["your_service"]` with a fallback in `src/config/ui_config.py`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_core.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Code Organization Rules

- **One responsibility per file**: Each file contains closely related functions, not one function per file
- **No circular imports**: Each layer imports only from layers below or at the same level
- **Session state keys**: Never rename existing `st.session_state` keys without updating all references
- **Caching**: Use `@st.cache_data` for data-returning functions, `@st.cache_resource` for resource objects
- **Error handling**: Use `src/utils/logging.py` `log_error()` for all error logging

## File Conventions

- Pages: `src/pages/` - each exports a single `render_*_tab()` or `render_*_page()` function
- Components: `src/components/` - reusable UI widgets, no data logic
- Processing: `src/processing/` - pure data transformation, no Streamlit UI calls
- Services: `src/services/` - external API communication
- Utils: `src/utils/` - stateless helper functions

## Debugging

- **System Logs**: Available in the sidebar under "Maintenance & Settings" > "System Logs"
- **Error log file**: `data/error_log.json`
- **Session state**: Inspect via Streamlit's built-in state viewer or `st.write(st.session_state)`
- **API issues**: Check secrets configuration in `.streamlit/secrets.toml`

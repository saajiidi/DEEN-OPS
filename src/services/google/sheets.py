import pandas as pd

from src.config.ui_config import DEFAULT_GSHEET_URL


def load_default_gsheet():
    """Load data from the default Google Sheet URL."""
    return pd.read_csv(DEFAULT_GSHEET_URL)

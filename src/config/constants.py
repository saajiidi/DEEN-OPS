import os

# Data directories
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
FEEDBACK_DIR = os.path.join(DATA_DIR, "feedback")
INCOMING_DIR = os.path.join(DATA_DIR, "incoming")
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources")

# Snapshot file paths
STOCK_SNAPSHOT_PATH = os.path.join(RESOURCES_DIR, "last_stock.csv")
SALES_SNAPSHOT_PATH = os.path.join(RESOURCES_DIR, "sales_snapshot.csv")

# Error log path
ERROR_LOG_FILE = os.path.join(DATA_DIR, "error_logs.json")

# Persistence
STATE_FILE = os.path.join(DATA_DIR, "session_state.json")

# Common category options for filter UI
COMMON_CATS = [
    "Tank Top", "Boxer", "Jeans", "Denim Shirt", "Flannel Shirt",
    "Polo Shirt", "Panjabi", "Trousers", "Joggers", "Twill Chino",
    "Mask", "Leather Bag", "Water Bottle", "Contrast Shirt",
    "Turtleneck", "Drop Shoulder", "Wallet", "Kaftan Shirt",
    "Active Wear", "Jersy", "Sweatshirt", "Jacket", "Belt",
    "Sweater", "Passport Holder", "Card Holder", "Cap",
    "HS T-Shirt", "FS T-Shirt", "HS Shirt", "FS Shirt"
]

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)
os.makedirs(INCOMING_DIR, exist_ok=True)
os.makedirs(RESOURCES_DIR, exist_ok=True)

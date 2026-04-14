# config.py - Configuration & Global Constants

LOGO_PNG = "assets/deen_logo.png"
FEEDBACK_DIR = "feedback"

# Category mapping for Sales Performance (Original broad categories)
SALES_CATEGORY_MAPPING = {
    'Boxer': ['boxer'],
    'Tank Top': ['tank top', 'tanktop', 'tank', 'top'],
    'Jeans': ['jeans'],
    'Denim Shirt': ['denim'],
    'Flannel Shirt': ['flannel'],
    'Polo Shirt': ['polo'],
    'Panjabi': ['panjabi', 'punjabi'],
    'Trousers': ['trousers', 'pant', 'cargo', 'trouser', 'joggers', 'track pant', 'jogger'],
    'Twill Chino': ['twill chino'],
    'Mask': ['mask'],
    'Water Bottle': ['water bottle'],
    'Contrast Shirt': ['contrast'],
    'Turtleneck': ['turtleneck', 'mock neck'],
    'Drop Shoulder': ['drop', 'shoulder'],
    'Wallet': ['wallet'],
    'Kaftan Shirt': ['kaftan'],
    'Active Wear': ['active wear'],
    'Jersy': ['jersy'],
    'Sweatshirt': ['sweatshirt', 'hoodie', 'pullover'],
    'Jacket': ['jacket', 'outerwear', 'coat'],
    'Belt': ['belt'],
    'Sweater': ['sweater', 'cardigan', 'knitwear'],
    'Passport Holder': ['passport holder'],
    'Cap': ['cap'],
    'Leather Bag': ['bag', 'backpack'],
}

# Category mapping for Stock Count (Detailed categories)
STOCK_CATEGORY_MAPPING = {
    "Jeans Slim Fit": lambda n: "jeans" in n and "slim fit" in n,
    "Jeans Regular Fit": lambda n: "jeans" in n and "regular fit" in n,
    "Jeans Straight Fit": lambda n: "jeans" in n and "straight fit" in n,
    "Panjabi": lambda n: "panjabi" in n,
    "Active Wear": lambda n: "active wear" in n,
    "T-shirt Basic Full": lambda n: "t-shirt" in n and "full sleeve" in n,
    "T-shirt Drop-Shoulder": lambda n: "t-shirt" in n and ("drop-shoulder" in n or "drop shoulder" in n),
    "T-shirt Basic Half": lambda n: "t-shirt" in n and not ("full sleeve" in n or "drop-shoulder" in n or "drop shoulder" in n),
    "Sweatshirt": lambda n: "sweatshirt" in n,
    "Turtle-Neck": lambda n: "turtle-neck" in n or "turtleneck" in n,
    "Tank-Top": lambda n: "tank-top" in n or "tank top" in n,
    "Trousers Cotton Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n) and ("twill" in n or "chino" in n or "cotton" in n),
    "Trousers Terry Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n),
    "Polo": lambda n: "polo" in n,
    "Kaftan Shirt": lambda n: "kaftan" in n,
    "Contrast Stich": lambda n: "contrast stitch" in n or "contrast stich" in n,
    "Denim Shirt": lambda n: "denim" in n and "shirt" in n,
    "Flannel Shirt": lambda n: "flannel" in n and "shirt" in n,
    "Casual Shirt Full": lambda n: "shirt" in n and "full sleeve" in n and not any(k in n for k in ["denim", "flannel", "kaftan", "contrast", "stitch", "stich", "polo", "sweatshirt"]),
    "Casual Shirt Half": lambda n: "shirt" in n and not any(k in n for k in ["full sleeve", "denim", "flannel", "kaftan", "contrast", "stitch", "stich", "polo", "t-shirt", "sweatshirt"]),
    "Belt": lambda n: "belt" in n,
    "Wallet Bifold": lambda n: "wallet" in n and "bifold" in n,
    "Wallet Trifold": lambda n: "wallet" in n and "trifold" in n,
    "Wallet Long": lambda n: "wallet" in n and "long" in n,
    "Passport Holder": lambda n: "passport holder" in n,
    "Mask": lambda n: "mask" in n,
    "Card Holder": lambda n: "card holder" in n,
    "Water Bottle": lambda n: "water bottle" in n,
    "Boxer": lambda n: "boxer" in n,
    "Bag": lambda n: "bag" in n,
}

COLUMN_ALIAS_MAPPING = {
    'name': ['item name', 'product name', 'product', 'item', 'title', 'description', 'name'],
    'cost': ['item cost', 'price', 'unit price', 'cost', 'rate', 'mrp', 'selling price', 'regular price'],
    'qty': ['quantity', 'qty', 'units', 'sold', 'count', 'total quantity', 'stock', 'inventory', 'stock quantity', 'quantity sold'],
    'date': ['date', 'order date', 'month', 'time', 'created at'],
    'order_id': ['order id', 'order #', 'invoice number', 'invoice #', 'order number', 'transaction id', 'id'],
    'phone': ['phone', 'contact', 'mobile', 'cell', 'phone number', 'customer phone']
}

import re
import functools

def _normalize(name):
    """Normalizes names for matching."""
    if not name: return ""
    return str(name).lower().strip()

def _has_any(keywords, text):
    """Checks if any keyword is in the text."""
    return any(kw in text for kw in keywords)

def get_category_for_sales(name) -> str:
    """Categorizes products based on keywords in their names (v14.1 Robust Rules)."""
    name_str = _normalize(name)
    if not name_str: return "Others"

    # v14.0 High-Priority Unique Categories
    if _has_any(["sweatshirt", "hoodie", "pullover"], name_str): return "Sweatshirt"
    if "polo" in name_str: return "Polo Shirt"
    if _has_any(["turtleneck", "turtle-neck", "mock neck"], name_str): return "Turtle-Neck"
    if "bundle" in name_str: return "Bundles"

    # v14.1 T-Shirt Cluster Redirection (Active Wear, Tank Top, etc.)
    if _has_any(["active wear", "activewear", "jersy", "jersey", "tank top"], name_str):
        return "T-Shirt"

    specific_cats = {
        "Boxer": ["boxer"],
        "Jeans": ["jeans"],
        "Panjabi": ["panjabi", "punjabi"],
        "Twill Chino": ["twill chino", "chino", "twill"],
        "Trousers": ["trousers", "trouser"],
        "Mask": ["mask"],
        "Leather Bag": ["bag", "backpack"],
        "Water Bottle": ["water bottle"],
        "Wallet": ["wallet"],
        "Belt": ["belt"],
        "Sweater": ["sweater", "cardigan", "knitwear"],
    }

    for cat, keywords in specific_cats.items():
        if _has_any(keywords, name_str):
            return cat

    fs_keywords = ["full sleeve", "long sleeve", "fs", "l/s", "fullsleeve"]
    if _has_any(["t-shirt", "t shirt", "tee"], name_str):
        return "T-Shirt"

    if _has_any(["shirt"], name_str):
        return "FS Shirt" if _has_any(fs_keywords, name_str) else "HS Shirt"

    # v14.1: Typo Resilience (Fuzzy Logic Fallback)
    from fuzzywuzzy import process
    all_targets = list(specific_cats.keys()) + ["Sweatshirt", "Polo Shirt", "Turtle-Neck", "T-Shirt", "FS Shirt", "HS Shirt"]
    match = process.extractOne(name_str, all_targets)
    if match and match[1] > 85:
        return match[0]

    return "Others"

def get_sub_category_for_sales(name, category) -> str:
    """Extracts sub-category based on v14.1 Hierarchical Rules."""
    name_str = _normalize(name)
    if not name_str: return category

    if category == "Jeans":
        if "regular" in name_str: return "Regular Fit Jeans"
        if "slim" in name_str: return "Slim Fit Jeans"
        if "straight" in name_str: return "Straight Fit Jeans"

    elif category == "T-Shirt":
        if "drop shoulder" in name_str: return "Drop Shoulder"
        if _has_any(["tank top"], name_str): return "Tank Top"
        if _has_any(["active wear", "activewear"], name_str): return "Active Wear"
        if _has_any(["jersy", "jersey"], name_str): return "Jersy"
        if _has_any(["full sleeve", "long sleeve", "fs"], name_str): return "FS-T-Shirt"
        return "HS T-Shirt"

    elif category == "FS Shirt":
        if "flannel" in name_str: return "Flannel Shirt"
        if "denim" in name_str: return "Denim Shirt"
        if "oxford" in name_str: return "Oxford Shirt"
        if "kaftan" in name_str: return "Kaftan Shirt"
        if "casual" in name_str: return "FS Casual Shirt"
        return "FS Shirt"

    elif category == "HS Shirt":
        if "contrast" in name_str: return "Contrast Shirt"
        if "casual" in name_str: return "HS Casual Shirt"
        return "HS Shirt"

    elif category == "Wallet":
        if "passport" in name_str: return "Passport Holder"
        if "card holder" in name_str: return "Card Holder"
        if "long" in name_str: return "Long Wallet"
        if "bifold" in name_str: return "Bifold Wallet"
        if "trifold" in name_str: return "Trifold Wallet"
        return "Wallet"

    elif category == "Panjabi":
        if "embroidered cotton panjabi" in name_str: return "Old Panjabi"
        return "Panjabi"

    elif category == "Sweatshirt":
        if "cotton terry" in name_str: return "Cotton Terry Sweatshirt"
        if "french terry" in name_str: return "French Terry Sweatshirt"
        return "Sweatshirt"

    elif category == "Twill Chino":
        if "pant" in name_str: return "Twill Chino Pant"
        if "joggers" in name_str: return "Twill Joggers"
        if "five pockets" in name_str: return "Five Pockets"
        return "Twill Chino"

    elif category == "Trousers":
        if "joggers" in name_str: return "Joggers"
        if "regular fit" in name_str: return "Cotton Trousers"
        return "Trousers"

    elif category == "Bundles":
        detected = []
        if "jeans" in name_str: detected.append("Jeans")
        if "shirt" in name_str: detected.append("Shirt")
        if "t-shirt" in name_str: detected.append("T-Shirt")
        return f"Bundle ({', '.join(detected)})" if detected else "Bundle"

    return category

import csv
import sys

file_path = r'h:\Catwise-Analytics\wc-product-export-4-4-2026-1775294924321.csv'

categories = {
    "Jeans Slim Fit": lambda n: "jeans" in n and "slim fit" in n,
    "Jeans Regular Fit": lambda n: "jeans" in n and "regular fit" in n,
    "Jeans Straight Fit": lambda n: "jeans" in n and "straight fit" in n,
    "Panjabi": lambda n: "panjabi" in n,
    "T-shirt Basic Full": lambda n: "t-shirt" in n and "full sleeve" in n,
    "T-shirt Drop-Shoulder": lambda n: "t-shirt" in n and ("drop-shoulder" in n or "drop shoulder" in n),
    "T-shirt Basic Half": lambda n: "t-shirt" in n and not ("full sleeve" in n or "drop-shoulder" in n or "drop shoulder" in n),
    "Sweatshirt": lambda n: "sweatshirt" in n,
    "Turtle-Neck": lambda n: "turtle-neck" in n or "turtleneck" in n,
    "Tank-Top": lambda n: "tank-top" in n or "tank top" in n,
    "Trousers Terry Fabric": lambda n: (("trouser" in n or "jogger" in n or "pant" in n) and "terry" in n),
    "Trousers Cotton Fabric": lambda n: ("trouser" in n or "jogger" in n or "pant" in n) and ("twill" in n or "chino" in n or "cotton" in n),
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
}

results = {cat: 0 for cat in categories}
unmatched = []

with open(file_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        p_type = row.get('Type', '').lower()
        if p_type not in ['variation', 'simple']:
            continue
        
        name = row.get('Name', '').lower()
        stock_str = row.get('Stock', '')
        try:
                stock = int(stock_str) if stock_str and stock_str.strip() else 0
        except ValueError:
                stock = 0
            
        matched_cat = None
        for cat, func in categories.items():
            if func(name):
                results[cat] += stock
                matched_cat = cat
                break
        
        if not matched_cat and stock > 0:
            unmatched.append(f"{name}: {stock}")

print("Category|Quantity")
print("---|---")
for cat in [
    "Jeans Slim Fit", "Jeans Regular Fit", "Jeans Straight Fit", "Panjabi",
    "T-shirt Basic Half", "T-shirt Basic Full", "T-shirt Drop-Shoulder", "Tank-Top",
    "Trousers Terry Fabric", "Trousers Cotton Fabric", "Polo",
    "Casual Shirt Half", "Casual Shirt Full", "Kaftan Shirt", "Contrast Stich",
    "Denim Shirt", "Flannel Shirt", "Belt", "Wallet Bifold", "Wallet Trifold",
    "Wallet Long", "Passport Holder", "Mask", "Card Holder", "Water Bottle",
    "Boxer", "Sweatshirt", "Turtle-Neck"
]:
    print(f"{cat}|{results.get(cat, 0)}")

if unmatched:
    print("\nUnmatched items with stock:")
    for u in unmatched[:20]:
        print(u)

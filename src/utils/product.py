import functools


def get_base_product_name(name: str) -> str:
    """Removes the size portion (e.g. ' - XL') from a product name for cleaner filter grouping."""
    if not name or " - " not in name:
        return name
    return str(name).rsplit(" - ", 1)[0]


def get_size_from_name(name: str) -> str:
    """Extracts the size attribute from a product name string."""
    if not name or " - " not in name:
        return "N/A"
    return str(name).rsplit(" - ", 1)[1]


@functools.lru_cache(maxsize=1024)
def get_category_from_name(name):
    """Determines the category of an item based on its name using expert rules."""
    from src.processing.categorization import get_category_for_sales
    return get_category_for_sales(name)

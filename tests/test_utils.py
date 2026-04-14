import pytest
from src.utils.product import get_base_product_name, get_size_from_name
from src.utils.text import normalize_city_name, peek_zone_from_address


class TestProductUtils:
    def test_get_base_product_name(self):
        assert get_base_product_name("Premium T-Shirt - XL") == "Premium T-Shirt"
        assert get_base_product_name("Plain Product") == "Plain Product"
        assert get_base_product_name("") == ""
        assert get_base_product_name(None) is None

    def test_get_base_product_name_multiple_hyphens(self):
        assert get_base_product_name("Drop Shoulder - Black - L") == "Drop Shoulder - Black"

    def test_get_size_from_name(self):
        assert get_size_from_name("Premium T-Shirt - XL") == "XL"
        assert get_size_from_name("Plain Product") == "N/A"
        assert get_size_from_name("") == "N/A"
        assert get_size_from_name(None) == "N/A"


class TestTextUtils:
    def test_normalize_city_iso_codes(self):
        assert normalize_city_name("BD-13") == "Dhaka"
        assert normalize_city_name("BD-60") == "Sylhet"
        assert normalize_city_name("BD-10") == "Chattogram"

    def test_normalize_city_special_mappings(self):
        assert normalize_city_name("brahmanbaria") == "B. Baria"
        assert normalize_city_name("narsingdi") == "Narshingdi"
        assert normalize_city_name("bogura") == "Bogra"
        assert normalize_city_name("chattogram") == "Chittagong"

    def test_normalize_city_title_case_fallback(self):
        assert normalize_city_name("some city") == "Some City"

    def test_normalize_city_empty(self):
        assert normalize_city_name("") == ""
        assert normalize_city_name(None) == ""

    def test_peek_zone_from_address(self):
        assert peek_zone_from_address("House 10, Mirpur 12, Dhaka") == "Mirpur"
        assert peek_zone_from_address("Sector 4, Uttara, Dhaka") == "Uttara"
        assert peek_zone_from_address("123 Random St, Unknown City") == ""

    def test_peek_zone_empty(self):
        assert peek_zone_from_address("") == ""
        assert peek_zone_from_address(None) == ""
        assert peek_zone_from_address("nan") == ""

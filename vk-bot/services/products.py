import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_FILE = BASE_DIR / "data" / "products.json"


def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)["products"]


def get_available_products():
    products = load_products()

    return [
        product
        for product in products
        if product.get("available", False)
    ]


def find_product_by_name(name):
    products = load_products()

    name = name.lower().strip()

    for product in products:
        if product["name"].lower() == name:
            return product

    return None
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PRICES_FILE = BASE_DIR / "data" / "prices.json"


def load_prices():
    with open(PRICES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_price_per_sheet(format_name, print_type, quantity):
    prices = load_prices()

    format_data = prices["printing"].get(format_name)

    if not format_data:
        return None

    price_ranges = format_data.get(print_type)

    if not price_ranges:
        return None

    for price_range in price_ranges:
        min_quantity = price_range["from"]
        max_quantity = price_range["to"]

        if quantity >= min_quantity:
            if max_quantity is None or quantity <= max_quantity:
                return price_range["price"]

    return None


def calculate_print_price(format_name, print_type, quantity):
    price_per_sheet = get_price_per_sheet(
        format_name,
        print_type,
        quantity
    )

    if price_per_sheet is None:
        return None

    total_price = price_per_sheet * quantity

    return {
        "quantity": quantity,
        "price_per_sheet": price_per_sheet,
        "total_price": total_price
    }
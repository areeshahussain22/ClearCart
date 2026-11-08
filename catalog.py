"""The demo store's products. All names are made up. Prices are in GBP.

Prices live only here, on the server. The browser and the AI never set a price.
"""

from decimal import Decimal

CURRENCY = "GBP"

PRODUCTS = [
    {"id": "p01", "name": "Blue ruled notebook, A5", "price": "4.50", "rating": 4.6, "category": "Stationery",
     "description": "80 pages, soft cover, ruled lines."},
    {"id": "p02", "name": "Black gel pens, pack of 5", "price": "3.20", "rating": 4.4, "category": "Stationery",
     "description": "Smooth 0.7 mm gel ink."},
    {"id": "p03", "name": "Large-print weekly planner", "price": "7.99", "rating": 4.7, "category": "Stationery",
     "description": "Bold 18 point text, high-contrast pages."},
    {"id": "p04", "name": "Braille label tape, 3 rolls", "price": "6.50", "rating": 4.5, "category": "Accessibility",
     "description": "Clear tape for labelling jars and boxes."},
    {"id": "p05", "name": "Talking kitchen timer", "price": "9.99", "rating": 4.3, "category": "Accessibility",
     "description": "Announces the time left out loud."},
    {"id": "p06", "name": "Bump dots, pack of 60", "price": "2.99", "rating": 4.8, "category": "Accessibility",
     "description": "Raised tactile dots for marking buttons."},
    {"id": "p07", "name": "Ceramic coffee mug, white", "price": "5.50", "rating": 4.2, "category": "Kitchen",
     "description": "350 ml, dishwasher safe."},
    {"id": "p08", "name": "Insulated water bottle, 500 ml", "price": "12.00", "rating": 4.6, "category": "Kitchen",
     "description": "Keeps drinks cold for 12 hours."},
    {"id": "p09", "name": "Non-slip cutting board", "price": "8.25", "rating": 4.4, "category": "Kitchen",
     "description": "Rubber edges, raised grip."},
    {"id": "p10", "name": "Herbal tea sampler, 20 bags", "price": "4.75", "rating": 4.1, "category": "Food",
     "description": "Mint, chamomile, ginger and lemon."},
    {"id": "p11", "name": "Dark chocolate bar, 100 g", "price": "1.99", "rating": 4.5, "category": "Food",
     "description": "70 percent cocoa."},
    {"id": "p12", "name": "Roasted almonds, 200 g", "price": "3.60", "rating": 4.3, "category": "Food",
     "description": "Lightly salted, resealable bag."},
    {"id": "p13", "name": "USB-C charging cable, 1 m", "price": "6.99", "rating": 4.2, "category": "Electronics",
     "description": "Braided cable with a ridged plug for easy feel."},
    {"id": "p14", "name": "Wireless earbuds", "price": "24.99", "rating": 4.0, "category": "Electronics",
     "description": "Up to 6 hours of battery."},
    {"id": "p15", "name": "Phone stand, adjustable", "price": "7.50", "rating": 4.4, "category": "Electronics",
     "description": "Folds flat, fits most phones."},
    {"id": "p16", "name": "Cotton tote bag", "price": "3.99", "rating": 4.6, "category": "Home",
     "description": "Strong handles, holds 10 kg."},
    {"id": "p17", "name": "Scented candle, lavender", "price": "8.99", "rating": 4.5, "category": "Home",
     "description": "Burns for about 30 hours."},
    {"id": "p18", "name": "Soft fleece blanket", "price": "15.00", "rating": 4.7, "category": "Home",
     "description": "130 by 170 cm, machine washable."},
    {"id": "p19", "name": "Hand cream, 75 ml", "price": "4.20", "rating": 4.3, "category": "Personal care",
     "description": "Unscented, for dry skin."},
    {"id": "p20", "name": "Reusable face masks, pack of 3", "price": "5.00", "rating": 4.1, "category": "Personal care",
     "description": "Washable cotton, adjustable ear loops."},
]

_BY_ID = {p["id"]: p for p in PRODUCTS}


def get(product_id):
    return _BY_ID.get(product_id)


def price_of(product_id):
    p = get(product_id)
    return Decimal(p["price"]) if p else None


def money(value):
    """Format for the screen, e.g. 4.5 -> '£4.50'."""
    return "£" + format(Decimal(value).quantize(Decimal("0.01")), "f")


def money_words(value):
    """Format for reading aloud, e.g. 4.50 -> '4 pounds 50'."""
    v = Decimal(value).quantize(Decimal("0.01"))
    pounds = int(v)
    pence = int((v - pounds) * 100)
    p_word = "pound" if pounds == 1 else "pounds"
    if pence == 0:
        return "%d %s" % (pounds, p_word)
    return "%d %s %d" % (pounds, p_word, pence)

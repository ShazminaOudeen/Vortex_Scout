"""Builds mock_skus.json: 200 Sri Lankan supermarket SKUs.

    python -m app.generator.build_catalog

Deterministic (fixed seed). The original starter SKUs s1-s7 are kept verbatim
because the anomaly engine, mock data and tests refer to them by id. The
remaining 193 get a popularity-weighted `base_rate` (expected sale lines per
open hour) calibrated so the whole catalog sums to TOTAL_BASE_RATE, which
yields ~1,330 sale lines on a plain weekday (see generate_mock_pos.py).
"""
import json
from pathlib import Path

import numpy as np

from app.generator.catalog import SKUS_PATH

TOTAL_BASE_RATE = 70.0  # x 19 weighted open hours = ~1,330 lines/weekday
SEED = 7

STARTERS = [  # s1-s7, unchanged from the original scaffold (id, barcode, name, ...)
    ("s1", "4791001000011", "Munchee Super Cream Cracker 490g", "Biscuits & Confectionery", "03", "3B", 70, 310, 395, 3.0),
    ("s2", "4791001000028", "Highland Fresh Milk 1L", "Chilled Dairy", "05", "5A", 32, 340, 420, 4.0),
    ("s3", "4791001000035", "Anchor Full Cream Milk Powder 400g", "Chilled Dairy", "05", "5C", 41, 780, 920, 2.5),
    ("s4", "4791001000042", "Keells Samba Rice 5kg", "Dry Staples", "01", "1A", 120, 1050, 1290, 3.5),
    ("s5", "4791001000059", "Lipton Yellow Label Tea 200g", "Tea & Beverages", "02", "2B", 60, 640, 790, 2.0),
    ("s6", "4791001000066", "Munchee Chocolate Cream Biscuits 85g", "Biscuits & Confectionery", "03", "3A", 90, 95, 130, 3.2),
    ("s7", "4791001000073", "Maliban Lemon Puff 200g", "Biscuits & Confectionery", "03", "3C", 55, 210, 275, 2.2),
]

# category -> (aisle, bays, total SKUs incl. starters, popularity weight, {brand: [(product, price LKR)]})
CATEGORIES: dict[str, tuple[str, list[str], int, float, dict[str, list[tuple[str, int]]]]] = {
    "Chilled Dairy": ("05", ["5A", "5B", "5C", "5D", "5E", "5F"], 40, 1.4, {
        "Highland": [("Fresh Milk 500ml", 230), ("Set Yoghurt 80g", 85), ("Curd 500ml", 480), ("Butter 200g", 780),
                     ("Cheese Slices 200g", 890), ("Strawberry Milk 180ml", 110), ("Chocolate Milk 180ml", 110),
                     ("UHT Milk 1L", 450)],
        "Anchor": [("Butter 227g", 1050), ("Cheese Block 250g", 1250), ("Full Cream Milk Powder 1kg", 2150),
                   ("Skimmed Milk Powder 400g", 880), ("Milk Powder 200g", 480), ("Instant Milk Tea Mix 250g", 520)],
        "Cargills": [("Fresh Milk 1L", 410), ("Yoghurt Drink 200ml", 120), ("Fruit Yoghurt 100g", 140),
                     ("Curd Pot 400ml", 360), ("Paneer 200g", 540), ("Cream 200ml", 480), ("Ghee 250g", 1100)],
        "Kotmale": [("Fresh Milk 1L", 430), ("Drinking Yoghurt 150ml", 100), ("Butter 200g", 760),
                    ("Vanilla Ice Milk 180ml", 120), ("Curd 450ml", 440), ("Cheese Spread 140g", 560)],
        "Ambewela": [("Fresh Milk 1L", 440), ("Yoghurt Cup 90g", 95), ("Cheese Slices 150g", 720),
                     ("Butter 100g", 410), ("Flavoured Milk 200ml", 130), ("Curd 500ml", 470)],
        "Pelwatte": [("Fresh Milk 1L", 420), ("Cheddar Cheese 200g", 980), ("Yoghurt Cup 80g", 80), ("Butter 100g", 420),
                     ("Condensed Milk 400g", 410), ("Evaporated Milk 410g", 360)],
    }),
    "Biscuits & Confectionery": ("03", ["3A", "3B", "3C", "3D", "3E", "3F"], 36, 1.3, {
        "Munchee": [("Lemon Puff 200g", 260), ("Marie Biscuits 400g", 330), ("Cheese Crackers 200g", 290),
                    ("Gold Cream Cracker 400g", 360), ("Chocolate Wafer 85g", 120), ("Ginger Nuts 200g", 240),
                    ("Coconut Biscuits 200g", 250), ("Milk Toffee 200g", 310)],
        "Maliban": [("Cream Crackers 500g", 380), ("Chocolate Puff 200g", 300), ("Marie 200g", 190),
                    ("Tikiri Marie 100g", 100), ("Cheese Bits 100g", 160), ("Milk Shortcake 200g", 270),
                    ("Orange Cream 200g", 250), ("Custard Cream 200g", 260)],
        "Ritzbury": [("Milk Chocolate 90g", 480), ("Dark Chocolate 90g", 520), ("Hazelnut Chocolate 90g", 540),
                     ("Fruit & Nut Chocolate 90g", 550), ("Chocolate Bar 40g", 220)],
        "Elephant House": [("Fruit Gums 150g", 280), ("Toffee Mix 200g", 320), ("Lollipops 12s", 180),
                           ("Jelly Cups 6s", 260), ("Mint Sweets 150g", 210)],
        "Cadbury": [("Dairy Milk 80g", 560), ("Chocolate Fingers 100g", 340)],
        "Perfetti": [("Mentos Roll 37g", 110), ("Fruit Chew 100g", 180), ("Chewing Gum 14g", 90)],
        "Nestle": [("KitKat 4 Finger", 190), ("Smarties Tube 38g", 150), ("Munch Bar 25g", 100)],
    }),
    "Dry Staples": ("01", ["1A", "1B", "1C", "1D"], 26, 1.0, {
        "Keells": [("Nadu Rice 5kg", 1180), ("Red Raw Rice 5kg", 1090), ("Samba Rice 1kg", 290), ("White Sugar 1kg", 330),
                   ("Red Dhal 500g", 390), ("Wheat Flour 1kg", 280), ("Chickpeas 500g", 460)],
        "Cargills": [("Basmati Rice 1kg", 720), ("Green Gram 500g", 530), ("Corn Flour 400g", 290), ("Semolina 500g", 250),
                     ("Coconut Oil 750ml", 1080), ("Sunflower Oil 1L", 1380)],
        "Araliya": [("Samba Rice 5kg", 1320), ("Nadu Rice 1kg", 240), ("Kekulu Rice 5kg", 1150), ("Rice Flour 1kg", 330)],
        "Nipuna": [("Red Rice 2kg", 440), ("Sugar 500g", 170), ("Salt 400g", 95), ("Dhal Tin 400g", 310)],
        "Rathna": [("Dried Sprats 100g", 360), ("Maldive Fish 50g", 480), ("Tamarind 200g", 190)],
        "Sathosa": [("Samba Rice 1kg", 270), ("Wheat Flour 1kg", 260), ("Red Dhal 500g", 370)],
    }),
    "Tea & Beverages": ("02", ["2A", "2B", "2C", "2D"], 22, 0.9, {
        "Lipton": [("Tea Bags 25s", 420), ("Green Tea 20s", 490), ("Black Tea 100g", 360), ("Ice Tea 330ml", 160)],
        "Dilmah": [("Premium Tea 200g", 760), ("Tea Bags 50s", 780), ("Earl Grey 25s", 590), ("Green Tea 20s", 480),
                   ("Ceylon Tea 400g", 1380)],
        "Zesta": [("Tea 200g", 640), ("Tea Bags 25s", 380)],
        "Watawala": [("Tea 400g", 1010), ("Premium Tea 100g", 420)],
        "Elephant House": [("Ginger Beer 1.5L", 360), ("Cream Soda 1L", 260), ("Orange Barley 750ml", 390),
                           ("Necto Syrup 750ml", 560), ("Lime Cordial 750ml", 520), ("EGB 500ml", 150)],
        "Nescafe": [("Classic Coffee 50g", 920), ("3in1 Coffee 10s", 540)],
        "Milo": [("Malted Drink 400g", 1180), ("Malted Drink 200g", 640)],
    }),
    "Spices & Condiments": ("04", ["4A", "4B", "4C"], 18, 0.6, {
        "Motha": [("Chilli Powder 100g", 320), ("Curry Powder 100g", 280), ("Turmeric 50g", 190), ("Pepper 50g", 360),
                  ("Cinnamon 25g", 240)],
        "MD": [("Tomato Sauce 400g", 380), ("Chilli Sauce 350g", 360), ("Soya Sauce 200ml", 220),
               ("Mango Chutney 400g", 440), ("Jam Mixed Fruit 500g", 520), ("Mayonnaise 270g", 480)],
        "Cargills": [("Curry Leaves Dried 20g", 90), ("Mustard Seed 100g", 140), ("Fennel Seed 100g", 150),
                     ("Cumin 100g", 230)],
        "Edinborough": [("Pickled Lime 350g", 390), ("Brinjal Pickle 350g", 410), ("Vinegar 750ml", 190)],
        "Heinz": [("Baked Beans 415g", 410), ("Tomato Ketchup 460g", 520)],
    }),
    "Snacks & Instant Noodles": ("06", ["6A", "6B", "6C"], 16, 1.0, {
        "Maggi": [("Chicken Noodles 73g", 130), ("Curry Noodles 73g", 130), ("Masala Noodles 73g", 130)],
        "Prima": [("Kottu Mee 75g", 140), ("Instant Noodles 70g", 120)],
        "Ceylon Biscuits": [("Chilli Murukku 100g", 190), ("Cassava Chips 150g", 280), ("Banana Chips 150g", 300)],
        "Keells": [("Potato Chips 80g", 260), ("Mixed Nuts 150g", 520), ("Cashew Roasted 100g", 680),
                   ("Popcorn 60g", 190)],
        "Lays": [("Salted Chips 52g", 210), ("Spicy Chips 52g", 210)],
        "Pringles": [("Original 107g", 780), ("Sour Cream 107g", 780)],
        "Bombay": [("Mixture 150g", 260)],
    }),
    "Frozen & Ready Meals": ("07", ["7A", "7B", "7C"], 14, 0.5, {
        "Keells": [("Chicken Sausages 340g", 890), ("Chicken Nuggets 400g", 1050), ("Fish Fingers 300g", 980),
                   ("Frozen Peas 500g", 440)],
        "Crysbro": [("Chicken Breast 500g", 1180), ("Chicken Drumsticks 500g", 940), ("Chicken Burger 4s", 760),
                    ("Chicken Meatballs 300g", 720)],
        "Cargills": [("Frozen Paratha 5s", 380), ("Frozen Mixed Veg 500g", 460), ("Fish Cutlets 6s", 540),
                     ("Pol Roti Mix 500g", 280)],
        "Elephant House": [("Vanilla Ice Cream 1L", 980), ("Chocolate Ice Cream 1L", 1020),
                           ("Ice Cream Cup 100ml", 120)],
    }),
    "Bakery & Breakfast": ("08", ["8A", "8B", "8C"], 12, 0.9, {
        "Cargills": [("Sliced Bread 450g", 170), ("Butter Cake 300g", 620), ("Fish Bun 1pc", 80), ("Egg Roll 1pc", 100)],
        "Keells": [("Corn Flakes 250g", 690), ("Oats 400g", 540), ("Wheat Bread Loaf 400g", 160)],
        "Kellogg's": [("Chocos 375g", 980), ("Cornflakes 475g", 1180)],
        "Maliban": [("Bread Rolls 6s", 240), ("Sandwich Loaf 450g", 190)],
        "Harischandra": [("Wheat Bread 450g", 175), ("Milk Bread 450g", 180)],
    }),
    "Household & Personal Care": ("09", ["9A", "9B", "9C", "9D"], 16, 0.6, {
        "Sunlight": [("Dishwash Liquid 500ml", 340), ("Laundry Soap 110g", 120), ("Washing Powder 1kg", 520)],
        "Lifebuoy": [("Soap 100g", 110), ("Handwash 200ml", 290)],
        "Signal": [("Toothpaste 120g", 280), ("Toothbrush 2s", 240)],
        "Velvet": [("Toilet Tissue 4 Rolls", 480), ("Facial Tissue 100s", 310), ("Kitchen Towel 2s", 520)],
        "Clogard": [("Toothpaste 100g", 260), ("Mouthwash 250ml", 540)],
        "Baby Cheramy": [("Baby Soap 75g", 150), ("Baby Powder 100g", 320)],
        "Rexona": [("Soap 100g", 105), ("Deodorant Roll-on 50ml", 420)],
        "Harpic": [("Toilet Cleaner 500ml", 440)],
    }),
}


def _ean13(body12: str) -> str:
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(body12))
    return body12 + str((10 - total % 10) % 10)


def build() -> list[dict]:
    rng = np.random.default_rng(SEED)
    rows = [
        {"id": i, "barcode": barcode, "name": name, "category": cat, "aisle": aisle, "bay": bay,
         "ledger_stock": stock, "unit_cost": cost, "unit_price": price, "base_rate": rate}
        for i, barcode, name, cat, aisle, bay, stock, cost, price, rate in STARTERS
    ]
    used = {r["name"] for r in rows}
    pending: list[dict] = []
    for cat, (aisle, bays, total, weight, brands) in CATEGORIES.items():
        have = sum(r["category"] == cat for r in rows)
        pool = [(b, p, price) for b, items in brands.items() for p, price in items
                if f"{b} {p}" not in used]
        picks = rng.permutation(len(pool))[: total - have]
        assert len(picks) == total - have, f"{cat}: need {total - have} more SKUs, pool has {len(pool)}"
        for j in sorted(picks):
            brand, product, price = pool[j]
            pending.append({"name": f"{brand} {product}", "category": cat, "aisle": aisle,
                            "bay": bays[len(pending) % len(bays)], "unit_price": price,
                            "weight": weight * float(np.clip(rng.lognormal(0, 0.6), 0.25, 3.0))})
    # popularity -> base_rate, calibrated to the catalog-wide total
    budget = TOTAL_BASE_RATE - sum(r["base_rate"] for r in rows)
    total_w = sum(p["weight"] for p in pending)
    for k, p in enumerate(pending, start=len(rows) + 1):
        margin = float(rng.uniform(0.18, 0.30))
        rows.append({
            "id": f"s{k}", "barcode": _ean13(f"4791001{k:05d}"), "name": p["name"], "category": p["category"],
            "aisle": p["aisle"], "bay": p["bay"], "ledger_stock": int(rng.integers(35, 160)),
            "unit_cost": round(p["unit_price"] / (1 + margin)), "unit_price": p["unit_price"],
            "base_rate": max(0.03, round(budget * p["weight"] / total_w, 3)),
        })
    # absorb rounding drift so the total is exact
    rows[-1]["base_rate"] = round(rows[-1]["base_rate"] + TOTAL_BASE_RATE - sum(r["base_rate"] for r in rows), 3)
    return rows


if __name__ == "__main__":
    rows = build()
    Path(SKUS_PATH).write_text("[\n" + ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n")
    print(f"Wrote {len(rows)} SKUs to {SKUS_PATH}")

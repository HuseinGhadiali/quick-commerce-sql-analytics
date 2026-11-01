"""Generate a synthetic quick-commerce (10-minute grocery delivery) dataset for India.

The data is fully synthetic. Patterns that are common in Indian quick commerce are
built in on purpose so the SQL analysis has something real to find:

* Festive demand spikes (Holi, Raksha Bandhan, Ganesh Chaturthi, Diwali, New Year's Eve)
* Mumbai monsoon (Jun-Sep) slowing deliveries; IPL evenings lifting snack orders
* Breakfast / staples / dinner / late-night "missions" that shape basket mix
* Customers bunching their cart just above the free-delivery threshold (Rs 199)
* A late first delivery shortening the customer's lifetime
* A couple of under-performing dark stores and a ramp-up period for new stores

Usage:  python src/generate_data.py --out data/raw --seed 42
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31 23:59:59")
FREE_DELIVERY_THRESHOLD = 199

CITIES = [
    # id, name, state, tier, customer share, stores
    (1, "Mumbai", "Maharashtra", "Tier 1", 0.22, 8),
    (2, "Delhi NCR", "Delhi", "Tier 1", 0.22, 8),
    (3, "Bengaluru", "Karnataka", "Tier 1", 0.20, 7),
    (4, "Hyderabad", "Telangana", "Tier 1", 0.11, 4),
    (5, "Pune", "Maharashtra", "Tier 1", 0.10, 4),
    (6, "Chennai", "Tamil Nadu", "Tier 1", 0.08, 3),
    (7, "Kolkata", "West Bengal", "Tier 1", 0.04, 2),
    (8, "Ahmedabad", "Gujarat", "Tier 2", 0.03, 2),
]

LOCALITIES = {
    "Mumbai": ["Andheri West", "Bandra", "Powai", "Lower Parel", "Malad", "Thane West", "Chembur", "Borivali"],
    "Delhi NCR": ["Saket", "Dwarka", "Gurugram Sec 49", "Noida Sec 62", "Lajpat Nagar", "Rohini", "Janakpuri", "Gurugram DLF 3"],
    "Bengaluru": ["Koramangala", "HSR Layout", "Indiranagar", "Whitefield", "Jayanagar", "Electronic City", "Hebbal"],
    "Hyderabad": ["Gachibowli", "Madhapur", "Kondapur", "Banjara Hills"],
    "Pune": ["Baner", "Kothrud", "Viman Nagar", "Hinjewadi"],
    "Chennai": ["Velachery", "Anna Nagar", "OMR Thoraipakkam"],
    "Kolkata": ["Salt Lake", "Ballygunge"],
    "Ahmedabad": ["Prahlad Nagar", "Satellite"],
}

# category -> list of (name, mrp, margin, seasonal_months or None, festive flag)
CATALOG = {
    "Fruits & Vegetables": [
        ("Banana Robusta 1 dozen", 70, 0.22, None, 0), ("Onion 1 kg", 45, 0.18, None, 0),
        ("Tomato Hybrid 500 g", 30, 0.20, None, 0), ("Potato 1 kg", 40, 0.18, None, 0),
        ("Coriander Leaves 100 g", 15, 0.30, None, 0), ("Green Chilli 100 g", 12, 0.30, None, 0),
        ("Apple Shimla 4 pc", 160, 0.20, None, 0), ("Lemon 250 g", 35, 0.25, None, 0),
        ("Ginger 100 g", 25, 0.25, None, 0), ("Cucumber 500 g", 30, 0.22, None, 0),
        ("Carrot Ooty 500 g", 40, 0.22, None, 0), ("Spinach 250 g", 25, 0.25, None, 0),
        ("Alphonso Mango 1 dozen", 899, 0.18, (4, 5, 6), 0), ("Pomegranate 2 pc", 140, 0.20, None, 0),
        ("Watermelon 1 pc", 90, 0.20, (3, 4, 5, 6), 0), ("Marigold Flowers 250 g", 60, 0.35, None, 1),
    ],
    "Dairy, Bread & Eggs": [
        ("Toned Milk 500 ml", 28, 0.06, None, 0), ("Full Cream Milk 1 L", 68, 0.06, None, 0),
        ("Curd 400 g", 45, 0.12, None, 0), ("Paneer 200 g", 90, 0.14, None, 0),
        ("Salted Butter 100 g", 58, 0.10, None, 0), ("Brown Bread 400 g", 55, 0.15, None, 0),
        ("White Bread 400 g", 45, 0.15, None, 0), ("Eggs 6 pc", 54, 0.12, None, 0),
        ("Eggs 12 pc", 99, 0.12, None, 0), ("Cheese Slices 200 g", 140, 0.14, None, 0),
        ("Masala Buttermilk 200 ml", 15, 0.15, (3, 4, 5, 6), 0), ("Cow Ghee 500 ml", 330, 0.10, None, 1),
    ],
    "Snacks & Munchies": [
        ("Classic Salted Chips 52 g", 20, 0.22, None, 0), ("Masala Chips 52 g", 20, 0.22, None, 0),
        ("Aloo Bhujia 400 g", 105, 0.20, None, 0), ("Nachos Cheese 150 g", 99, 0.24, None, 0),
        ("Choco Chip Cookies 150 g", 60, 0.22, None, 0), ("Cream Biscuits 120 g", 30, 0.20, None, 0),
        ("Roasted Makhana 80 g", 120, 0.30, None, 0), ("Peanut Chikki 200 g", 70, 0.28, (1, 12), 0),
        ("Methi Khakhra 200 g", 85, 0.26, None, 0), ("Butter Popcorn 60 g", 40, 0.26, None, 0),
        ("Milk Chocolate Bar 50 g", 50, 0.20, None, 0), ("Mixture Namkeen 200 g", 55, 0.22, None, 0),
        ("Kaju Katli 250 g", 350, 0.30, None, 1), ("Dry Fruit Gift Box 500 g", 799, 0.32, None, 1),
    ],
    "Beverages": [
        ("Cola 750 ml", 40, 0.18, None, 0), ("Lemon Soda 600 ml", 35, 0.18, None, 0),
        ("Mango Drink 1.2 L", 70, 0.18, (3, 4, 5, 6), 0), ("Packaged Water 1 L", 20, 0.25, None, 0),
        ("Cold Coffee 200 ml", 45, 0.22, None, 0), ("Energy Drink 250 ml", 125, 0.20, None, 0),
        ("Tender Coconut Water 200 ml", 50, 0.20, (3, 4, 5, 6), 0), ("Masala Chai Premix 10 sachets", 120, 0.25, None, 0),
        ("Instant Coffee 50 g", 180, 0.18, None, 0), ("Green Tea 25 bags", 160, 0.25, None, 0),
        ("Orange Juice 1 L", 125, 0.18, None, 0), ("Tonic Water 300 ml", 80, 0.22, None, 0),
    ],
    "Atta, Rice & Dal": [
        ("Whole Wheat Atta 5 kg", 275, 0.08, None, 0), ("Basmati Rice 1 kg", 160, 0.10, None, 0),
        ("Sona Masoori Rice 5 kg", 380, 0.08, None, 0), ("Toor Dal 1 kg", 180, 0.08, None, 0),
        ("Moong Dal 500 g", 80, 0.10, None, 0), ("Chana Dal 1 kg", 110, 0.10, None, 0),
        ("Sugar 1 kg", 50, 0.06, None, 0), ("Iodised Salt 1 kg", 28, 0.10, None, 0),
        ("Sunflower Oil 1 L", 155, 0.07, None, 0), ("Mustard Oil 1 L", 175, 0.07, None, 0),
        ("Poha 500 g", 45, 0.15, None, 0), ("Besan 500 g", 65, 0.12, None, 1),
    ],
    "Instant & Frozen": [
        ("Instant Noodles 4-pack", 56, 0.16, None, 0), ("Cup Noodles 70 g", 50, 0.18, None, 0),
        ("Frozen Green Peas 500 g", 95, 0.22, None, 0), ("Frozen Paratha 5 pc", 110, 0.24, None, 0),
        ("Ready-to-eat Dal Makhani 300 g", 125, 0.24, None, 0), ("Penne Pasta 500 g", 99, 0.22, None, 0),
        ("Tomato Ketchup 950 g", 140, 0.18, None, 0), ("Frozen French Fries 400 g", 120, 0.24, None, 0),
        ("Vanilla Ice Cream 700 ml", 199, 0.25, (3, 4, 5, 6), 0), ("Rolled Oats 1 kg", 199, 0.20, None, 0),
    ],
    "Personal Care": [
        ("Bath Soap 4 x 100 g", 180, 0.24, None, 0), ("Anti-dandruff Shampoo 340 ml", 380, 0.28, None, 0),
        ("Toothpaste 150 g", 110, 0.22, None, 0), ("Toothbrush 2 pc", 90, 0.30, None, 0),
        ("Face Wash 100 ml", 199, 0.30, None, 0), ("Body Lotion 400 ml", 350, 0.30, (11, 12, 1, 2), 0),
        ("Sanitary Pads 20 pc", 210, 0.26, None, 0), ("Shaving Foam 200 g", 230, 0.28, None, 0),
        ("Deodorant 150 ml", 260, 0.32, None, 0), ("Hand Wash Refill 750 ml", 120, 0.28, None, 0),
        ("Sunscreen SPF 50 50 g", 399, 0.32, (3, 4, 5, 6), 0),
    ],
    "Home Care & Puja": [
        ("Dishwash Liquid 750 ml", 175, 0.20, None, 0), ("Detergent Powder 1 kg", 130, 0.18, None, 0),
        ("Liquid Detergent 2 L", 420, 0.22, None, 0), ("Floor Cleaner 1 L", 210, 0.24, None, 0),
        ("Toilet Cleaner 500 ml", 99, 0.24, None, 0), ("Garbage Bags 30 pc", 99, 0.32, None, 0),
        ("Mosquito Repellent Refill", 85, 0.26, (6, 7, 8, 9), 0), ("Kitchen Towels 2 rolls", 120, 0.28, None, 0),
        ("Agarbatti 100 sticks", 60, 0.35, None, 1), ("Clay Diya Set 12 pc", 149, 0.40, None, 1),
        ("Rangoli Colours 10 shades", 199, 0.40, None, 1), ("Puja Samagri Kit", 299, 0.38, None, 1),
    ],
}

MISSIONS = {
    # mission: category weights
    "breakfast": {"Dairy, Bread & Eggs": 0.45, "Fruits & Vegetables": 0.28, "Beverages": 0.12,
                  "Atta, Rice & Dal": 0.05, "Snacks & Munchies": 0.05, "Personal Care": 0.05},
    "staples": {"Atta, Rice & Dal": 0.24, "Fruits & Vegetables": 0.20, "Home Care & Puja": 0.15,
                "Personal Care": 0.14, "Dairy, Bread & Eggs": 0.15, "Instant & Frozen": 0.08, "Beverages": 0.04},
    "dinner": {"Snacks & Munchies": 0.24, "Beverages": 0.18, "Instant & Frozen": 0.18,
               "Fruits & Vegetables": 0.14, "Dairy, Bread & Eggs": 0.18, "Atta, Rice & Dal": 0.08},
    "late_night": {"Snacks & Munchies": 0.45, "Beverages": 0.30, "Instant & Frozen": 0.20, "Personal Care": 0.05},
}

# product affinities: if the first product is in the basket, add the second with probability p
AFFINITIES = [
    ("Brown Bread 400 g", "Eggs 6 pc", 0.35), ("White Bread 400 g", "Salted Butter 100 g", 0.35),
    ("Classic Salted Chips 52 g", "Cola 750 ml", 0.40), ("Masala Chips 52 g", "Cola 750 ml", 0.35),
    ("Instant Noodles 4-pack", "Tomato Ketchup 950 g", 0.15), ("Nachos Cheese 150 g", "Cola 750 ml", 0.35),
    ("Onion 1 kg", "Tomato Hybrid 500 g", 0.45), ("Tomato Hybrid 500 g", "Coriander Leaves 100 g", 0.30),
    ("Frozen French Fries 400 g", "Tomato Ketchup 950 g", 0.35), ("Penne Pasta 500 g", "Cheese Slices 200 g", 0.30),
    ("Clay Diya Set 12 pc", "Rangoli Colours 10 shades", 0.45), ("Puja Samagri Kit", "Marigold Flowers 250 g", 0.50),
    ("Whole Wheat Atta 5 kg", "Toor Dal 1 kg", 0.30), ("Energy Drink 250 ml", "Milk Chocolate Bar 50 g", 0.20),
]

FESTIVALS = {  # date -> (demand multiplier, days of lead-up)
    "2024-03-25": (1.5, 2),   # Holi
    "2024-08-19": (1.3, 1),   # Raksha Bandhan
    "2024-09-07": (1.4, 2),   # Ganesh Chaturthi
    "2024-11-01": (1.9, 5),   # Diwali
    "2024-12-31": (1.6, 0),   # New Year's Eve
    "2025-03-14": (1.5, 2),   # Holi
    "2025-08-09": (1.3, 1),   # Raksha Bandhan
    "2025-08-27": (1.4, 2),   # Ganesh Chaturthi
    "2025-10-20": (1.9, 5),   # Diwali
    "2025-12-31": (1.6, 0),   # New Year's Eve
}
IPL_SEASONS = [(pd.Timestamp("2024-03-22"), pd.Timestamp("2024-05-26")),
               (pd.Timestamp("2025-03-22"), pd.Timestamp("2025-06-03"))]

CHANNELS = ["Organic", "Referral", "Paid Social", "Google Ads", "Offline Promo"]
CHANNEL_P = [0.35, 0.14, 0.26, 0.15, 0.10]
CHANNEL_LIFE_DAYS = {"Organic": 170, "Referral": 230, "Paid Social": 70, "Google Ads": 130, "Offline Promo": 100}
CHANNEL_RATE = {"Organic": 1.0, "Referral": 1.2, "Paid Social": 0.8, "Google Ads": 0.95, "Offline Promo": 0.85}

HOUR_WEIGHTS = np.array([1.4, 1.0, 0.6, 0.3, 0.2, 0.3, 1.2, 3.0, 4.6, 4.8, 3.6, 3.2,
                         3.4, 3.0, 2.6, 2.6, 3.0, 4.2, 5.4, 6.2, 6.0, 5.0, 3.6, 2.4])


def day_weights(days: pd.DatetimeIndex) -> np.ndarray:
    """Relative order demand for each calendar day (weekend + festive effects)."""
    w = np.ones(len(days))
    dow = days.day_of_week.to_numpy()
    w *= np.where(dow >= 5, 1.18, 1.0)
    w *= np.where(days.day.to_numpy() <= 5, 1.08, 1.0)  # salary-week staples top-up
    for d, (mult, lead) in FESTIVALS.items():
        d = pd.Timestamp(d)
        for k in range(lead + 1):
            w = np.where(days == d - pd.Timedelta(days=k), w * (mult if k == 0 else 1 + (mult - 1) * 0.6), w)
    return w


def build_dimensions(rng: np.random.Generator):
    cities = pd.DataFrame(CITIES, columns=["city_id", "city_name", "state", "city_tier", "share", "n_stores"])

    stores = []
    sid = 101
    for c in cities.itertuples():
        for i in range(c.n_stores):
            # most stores open before 2025; roughly one in five launches during the year
            if rng.random() < 0.25 and i > 0:
                launch = START + pd.Timedelta(days=int(rng.integers(90, 640)))
            else:
                launch = START - pd.Timedelta(days=int(rng.integers(90, 700)))
            stores.append((sid, c.city_id, f"{c.city_name.split()[0][:3].upper()}-{LOCALITIES[c.city_name][i][:12].replace(' ', '')}",
                           LOCALITIES[c.city_name][i], launch.date(), int(rng.integers(2500, 4500))))
            sid += 1
    stores = pd.DataFrame(stores, columns=["store_id", "city_id", "store_code", "locality", "launch_date", "area_sqft"])
    # store-level operational quality: two chronically slow stores
    stores["_ops_penalty"] = rng.normal(0, 0.8, len(stores))
    stores.loc[stores["store_code"].str.contains("Andheri|Whitefield"), "_ops_penalty"] += 3.5

    rows = []
    pid = 1001
    for cat, items in CATALOG.items():
        for name, mrp, margin, season, festive in items:
            disc = float(rng.choice([0, 0.05, 0.08, 0.10, 0.15], p=[0.35, 0.2, 0.2, 0.15, 0.1]))
            sp = round(mrp * (1 - disc))
            cost = round(sp * (1 - margin), 2)
            rows.append((pid, name, cat, mrp, sp, cost, 0, season, festive))
            pid += 1
            # private-label twin for high-volume staples/snacks: cheaper and higher margin
            if cat in ("Atta, Rice & Dal", "Snacks & Munchies", "Home Care & Puja") and rng.random() < 0.35:
                sp2 = round(sp * 0.85)
                rows.append((pid, f"Basket Basics {name}", cat, round(mrp * 0.9), sp2,
                             round(sp2 * (1 - margin - 0.12), 2), 1, season, festive))
                pid += 1
    products = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "mrp", "selling_price",
                                           "unit_cost", "is_private_label", "_season", "_festive"])
    # long-tail popularity within category
    products["_pop"] = rng.pareto(1.6, len(products)) + 0.3
    products.loc[products["is_private_label"] == 1, "_pop"] *= 0.5
    return cities, stores, products


def simulate(seed: int = 42, n_customers: int = 38000):
    rng = np.random.default_rng(seed)
    cities, stores, products = build_dimensions(rng)
    days = pd.date_range(START, END.normalize(), freq="D")
    dw = day_weights(days)

    # ---------------- customers ----------------
    trend = np.linspace(0.5, 1.5, len(days))           # the business is growing
    signup_w = trend * dw * np.where(days.month.isin([10, 11]), 1.3, 1.0)
    signup_w[-14:] = 0                                   # nobody signs up in the last two weeks
    signup_idx = rng.choice(len(days), n_customers, p=signup_w / signup_w.sum())
    city_id = rng.choice(cities.city_id, n_customers, p=cities.share / cities.share.sum())
    channel = rng.choice(CHANNELS, n_customers, p=CHANNEL_P)
    customers = pd.DataFrame({
        "customer_id": np.arange(1, n_customers + 1),
        "city_id": city_id,
        "signup_date": days[signup_idx],
        "acquisition_channel": channel,
        "age_band": rng.choice(["18-24", "25-34", "35-44", "45+"], n_customers, p=[0.22, 0.45, 0.22, 0.11]),
    })
    # home store: an open store in the same city (stores launched after signup are excluded)
    store_launch = pd.to_datetime(stores.launch_date)
    home = np.empty(n_customers, dtype=int)
    for cid, grp in customers.groupby("city_id"):
        cs = stores[stores.city_id == cid]
        cl = store_launch[cs.index].to_numpy()
        for idx, sdate in zip(grp.index, grp.signup_date.to_numpy()):
            open_ = cs.store_id.to_numpy()[cl <= sdate]
            home[idx] = rng.choice(open_)
    customers["_home_store"] = home

    life = np.array([rng.exponential(CHANNEL_LIFE_DAYS[c]) for c in channel])
    rate = rng.gamma(0.9, 0.85, n_customers) * np.array([CHANNEL_RATE[c] for c in channel])  # orders / week

    # ---------------- first orders (one per customer, on signup day) ----------------
    first = pd.DataFrame({"customer_id": customers.customer_id, "store_id": home,
                          "order_date": customers.signup_date, "is_first": 1})
    first_del = _delivery_minutes(first, stores, rng)
    late_first = (first_del["actual"] - first_del["promised"]) > 4
    late_small = ((first_del["actual"] - first_del["promised"]) > 0) & ~late_first
    life = np.where(late_first, life * 0.45, np.where(late_small, life * 0.8, life))  # bad first experience hurts

    # ---------------- repeat orders via thinned Poisson process ----------------
    end_day = np.minimum(customers.signup_date.to_numpy() + (life * 86400e9).astype("timedelta64[ns]"),
                         np.datetime64(END.normalize()))
    span_days = np.maximum((end_day - customers.signup_date.to_numpy()) / np.timedelta64(1, "D"), 0)
    wmax = dw.max()
    n_cand = rng.poisson(rate * span_days / 7 * wmax / dw.mean())
    cust_rep = np.repeat(customers.customer_id.to_numpy(), n_cand)
    start_rep = np.repeat(customers.signup_date.to_numpy(), n_cand)
    span_rep = np.repeat(span_days, n_cand)
    offs = np.ceil(rng.random(len(cust_rep)) * span_rep).astype(int)
    odate = start_rep + offs.astype("timedelta64[D]")
    day_index = ((odate - np.datetime64(START)) / np.timedelta64(1, "D")).astype(int)
    keep = rng.random(len(cust_rep)) < dw[np.clip(day_index, 0, len(days) - 1)] / wmax
    keep &= offs > 0
    repeat = pd.DataFrame({"customer_id": cust_rep[keep], "order_date": odate[keep], "is_first": 0})
    repeat["store_id"] = home[repeat.customer_id.to_numpy() - 1]

    orders = pd.concat([first, repeat], ignore_index=True)
    orders = orders[orders.order_date <= END].copy()
    orders["_city"] = stores.set_index("store_id").loc[orders.store_id, "city_id"].to_numpy()

    # time of day (IPL evenings tilt orders toward 7-11 pm)
    hw = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()
    hours = rng.choice(24, len(orders), p=hw)
    ipl = np.zeros(len(orders), dtype=bool)
    for a, b in IPL_SEASONS:
        ipl |= ((orders.order_date >= a) & (orders.order_date <= b)).to_numpy()
    swap = ipl & (rng.random(len(orders)) < 0.12)
    hours[swap] = rng.choice([19, 20, 21, 22], swap.sum())
    orders["order_ts"] = (orders.order_date + pd.to_timedelta(hours, unit="h")
                          + pd.to_timedelta(rng.integers(0, 3600, len(orders)), unit="s"))
    orders = orders.sort_values("order_ts").reset_index(drop=True)
    orders["order_id"] = np.arange(5_000_001, 5_000_001 + len(orders))
    orders["_hour"] = orders.order_ts.dt.hour
    in_ipl = np.zeros(len(orders), dtype=bool)
    for a, b in IPL_SEASONS:
        in_ipl |= ((orders.order_ts >= a) & (orders.order_ts <= b + pd.Timedelta(days=1))).to_numpy()
    orders["_ipl"] = in_ipl & orders._hour.between(19, 23).to_numpy()

    items = _baskets(orders, products, rng)
    first_del.index = customers.customer_id.to_numpy()
    deliveries, orders = _deliveries_and_status(orders, stores, rng, first_del)
    orders = _pricing(orders, items, rng)

    # order_ts must be inside store opening; drop the odd order placed before a store's launch
    orders = orders.merge(stores[["store_id", "launch_date"]], on="store_id")
    orders = orders[orders.order_ts >= pd.to_datetime(orders.launch_date)].drop(columns="launch_date")
    items = items[items.order_id.isin(orders.order_id)]
    deliveries = deliveries[deliveries.order_id.isin(orders.order_id)]

    customers = customers.merge(cities[["city_id"]], on="city_id")
    out = {
        "cities": cities.drop(columns=["share", "n_stores"]),
        "dark_stores": stores.drop(columns=[c for c in stores.columns if c.startswith("_")]),
        "customers": customers.drop(columns=[c for c in customers.columns if c.startswith("_")]),
        "products": products.drop(columns=[c for c in products.columns if c.startswith("_")]),
        "orders": orders[["order_id", "customer_id", "store_id", "order_ts", "order_status", "cancel_reason",
                          "payment_method", "coupon_code", "item_total", "discount_amount", "delivery_fee",
                          "order_value"]],
        "order_items": items[["order_id", "product_id", "quantity", "unit_price", "unit_cost"]],
        "deliveries": deliveries,
    }
    out["customers"]["signup_date"] = out["customers"]["signup_date"].dt.date
    return out


def _delivery_minutes(df: pd.DataFrame, stores: pd.DataFrame, rng, hours=None):
    n = len(df)
    st = stores.set_index("store_id")
    city = st.loc[df.store_id, "city_id"].to_numpy()
    penalty = st.loc[df.store_id, "_ops_penalty"].to_numpy()
    launch = pd.to_datetime(st.loc[df.store_id, "launch_date"]).to_numpy()
    d = pd.to_datetime(df["order_date"]).dt.normalize().to_numpy()
    month = pd.DatetimeIndex(d).month.to_numpy()
    hours = np.full(n, 12) if hours is None else hours

    dist_scale = np.array([0, 0.8, 1.15, 1.1, 1.05, 1.0, 1.0, 0.9, 1.25])[city]  # Mumbai is dense
    dist = np.clip(rng.gamma(2.2, 0.75, n) * dist_scale, 0.3, 6.5)
    promised = np.where(dist <= 1.6, 10, np.where(dist <= 3.2, 15, 20))
    prep = 2.6 + rng.gamma(2.0, 0.8, n)
    travel = dist * 3.0 + rng.normal(0, 1.0, n)
    peak = np.where(np.isin(hours, [8, 9, 19, 20, 21]), 1.6, 0)
    # monsoon: Mumbai is hit hard Jun-Sep, other cities moderately Jul-Sep; rain is day-level
    day_key = (d.astype("datetime64[D]").astype(int) * 31 + city) % 1000
    rainy = np.where(city == 1, (np.isin(month, [6, 7, 8, 9])) & (day_key < 450),
                     (np.isin(month, [7, 8, 9])) & (day_key < 150))
    rain = np.where(rainy, np.where(city == 1, rng.normal(6.5, 2.0, n), rng.normal(3.0, 1.0, n)), 0)
    festive = np.zeros(n)
    for f, (mult, lead) in FESTIVALS.items():
        fd = np.datetime64(f)
        festive += np.where((d >= fd - np.timedelta64(lead, "D")) & (d <= fd), 2.5 * (mult - 1) * 2, 0)
    age = (d - launch) / np.timedelta64(1, "D")
    ramp = np.where(age < 45, 3.5 * (1 - np.clip(age, 0, 45) / 45), 0)
    actual = np.clip(prep + travel + peak + rain + festive + ramp + penalty, 4, None)
    return pd.DataFrame({"distance_km": dist.round(2), "promised": promised, "actual": actual.round(1),
                         "rainy": rainy, "peak": peak > 0})


def _baskets(orders: pd.DataFrame, products: pd.DataFrame, rng) -> pd.DataFrame:
    month = orders.order_ts.dt.month.to_numpy()
    h = orders._hour.to_numpy()
    mission = np.select([(h >= 6) & (h < 11), (h >= 11) & (h < 17), (h >= 17) & (h < 23)],
                        ["breakfast", "staples", "dinner"], "late_night")
    mission = np.where(orders._ipl.to_numpy() & (rng.random(len(orders)) < 0.5), "late_night", mission)
    size = 1 + rng.poisson(2.6, len(orders))
    size = np.where(mission == "staples", size + rng.poisson(1.5, len(orders)), size)
    city_bonus = orders._city.map({1: 0.5, 2: 0.3, 3: 0.7, 4: 0.2, 5: 0.1, 6: 0.0, 7: -0.3, 8: -0.4}).to_numpy()
    size = np.maximum(1, size + np.round(rng.normal(city_bonus, 0.3)).astype(int))

    # festive orders: lots of puja / sweets / dry fruit in the run-up to festivals
    d = orders.order_ts.dt.normalize()
    fest = np.zeros(len(orders), dtype=bool)
    for f, (_, lead) in FESTIVALS.items():
        fd = pd.Timestamp(f)
        fest |= ((d >= fd - pd.Timedelta(days=lead + 2)) & (d <= fd)).to_numpy()
    fest &= ~d.dt.strftime("%m-%d").eq("12-31").to_numpy()

    cat_index = {c: products.index[products.category == c].to_numpy() for c in CATALOG}
    pop = products._pop.to_numpy()
    season = products._season.to_numpy()
    festive_flag = products._festive.to_numpy()
    name_to_pid = dict(zip(products.product_name, products.product_id))
    pid_arr = products.product_id.to_numpy()

    # pre-compute month-specific sampling weights per category
    weights = {}
    for m in range(1, 13):
        for c, idx in cat_index.items():
            w = pop[idx].copy()
            for j, i in enumerate(idx):
                if season[i] is not None:
                    w[j] *= 3.0 if m in season[i] else 0.0
                if festive_flag[i]:
                    w[j] *= 0.15
            weights[(m, c, False)] = w / w.sum()
            wf = w.copy()
            wf[festive_flag[idx] == 1] *= 12
            weights[(m, c, True)] = wf / wf.sum()

    rows_o, rows_p = [], []
    mission_cats = {k: (list(v.keys()), np.array(list(v.values())) / sum(v.values())) for k, v in MISSIONS.items()}
    for i in range(len(orders)):
        cats, cp = mission_cats[mission[i]]
        chosen = set()
        for c in rng.choice(cats, size[i], p=cp):
            idx = cat_index[c]
            chosen.add(pid_arr[idx[rng.choice(len(idx), p=weights[(month[i], c, bool(fest[i]))])]])
        if fest[i] and rng.random() < 0.35:
            c = rng.choice(["Home Care & Puja", "Snacks & Munchies", "Fruits & Vegetables"])
            idx = cat_index[c]
            chosen.add(pid_arr[idx[rng.choice(len(idx), p=weights[(month[i], c, True)])]])
        rows_o.extend([orders.order_id.iat[i]] * len(chosen))
        rows_p.extend(chosen)
    items = pd.DataFrame({"order_id": rows_o, "product_id": rows_p})

    # affinity add-ons (vectorised per rule)
    adds = []
    for a, b, p in AFFINITIES:
        if a not in name_to_pid or b not in name_to_pid:
            continue
        has_a = items.loc[items.product_id == name_to_pid[a], "order_id"].unique()
        pick = has_a[rng.random(len(has_a)) < p]
        adds.append(pd.DataFrame({"order_id": pick, "product_id": name_to_pid[b]}))
    items = pd.concat([items, *adds]).drop_duplicates(["order_id", "product_id"])
    items["quantity"] = rng.choice([1, 2, 3, 4], len(items), p=[0.78, 0.16, 0.04, 0.02])
    pr = products.set_index("product_id")
    items["unit_price"] = pr.loc[items.product_id, "selling_price"].to_numpy()
    items["unit_cost"] = pr.loc[items.product_id, "unit_cost"].to_numpy()

    # free-delivery bunching: carts just under Rs 199 often get a cheap top-up item
    tot = (items.unit_price * items.quantity).groupby(items.order_id).sum()
    near = tot[(tot >= 140) & (tot < FREE_DELIVERY_THRESHOLD)].index.to_numpy()
    near = near[rng.random(len(near)) < 0.55]
    if len(near):
        need = FREE_DELIVERY_THRESHOLD - tot.loc[near].to_numpy()
        cheap = products[(products.category.isin(["Snacks & Munchies", "Beverages", "Dairy, Bread & Eggs"]))
                         & (products._festive == 0) & (products._season.isna())]
        cheap = cheap.sort_values("selling_price")
        prices = cheap.selling_price.to_numpy()
        pos = np.searchsorted(prices, need, side="left")
        pos = np.minimum(pos + rng.integers(0, 4, len(pos)), len(prices) - 1)
        t = pd.DataFrame({"order_id": near, "product_id": cheap.product_id.to_numpy()[pos], "quantity": 1,
                          "unit_price": prices[pos], "unit_cost": cheap.unit_cost.to_numpy()[pos]})
        items = pd.concat([items, t])
        items = items.groupby(["order_id", "product_id"], as_index=False).agg(
            quantity=("quantity", "sum"), unit_price=("unit_price", "first"), unit_cost=("unit_cost", "first"))
    return items.sort_values(["order_id", "product_id"]).reset_index(drop=True)


def _deliveries_and_status(orders, stores, rng, first_del):
    dm = _delivery_minutes(orders.assign(order_date=orders.order_ts), stores, rng, hours=orders._hour.to_numpy())
    # first orders keep the delivery outcome that already shaped the customer's lifetime
    is_first = orders.is_first.to_numpy() == 1
    fd = first_del.loc[orders.customer_id.to_numpy()[is_first]]
    for col in ["distance_km", "promised", "actual", "rainy"]:
        dm.loc[is_first, col] = fd[col].to_numpy()
    n = len(orders)
    p_rider = 0.006 + 0.03 * dm.rainy + 0.01 * dm.peak
    p_cust = 0.015 + 0.01 * (dm.actual > dm.promised + 5)
    p_oos = np.full(n, 0.012)
    u = rng.random(n)
    status = np.where(u < p_rider, "Cancelled", np.where(u < p_rider + p_cust, "Cancelled",
                      np.where(u < p_rider + p_cust + p_oos, "Cancelled", "Delivered")))
    reason = np.where(u < p_rider, "Rider unavailable", np.where(u < p_rider + p_cust, "Customer cancelled",
                      np.where(u < p_rider + p_cust + p_oos, "Item out of stock", None)))
    orders = orders.copy()
    orders["order_status"] = status
    orders["cancel_reason"] = reason
    delivered = status == "Delivered"
    late_by = dm.actual - dm.promised
    rated = rng.random(n) < 0.55
    rating = np.clip(np.round(4.7 - 0.22 * np.clip(late_by, 0, None) + rng.normal(0, 0.6, n)), 1, 5)
    bad_item = rng.random(n) < 0.025                       # damaged / wrong item, independent of speed
    rating = np.where(bad_item, rng.choice([1, 2], n), rating)
    st = stores.set_index("store_id")
    riders = (orders.store_id.to_numpy() * 100 + rng.integers(1, 26, n))
    deliveries = pd.DataFrame({
        "order_id": orders.order_id.to_numpy(),
        "rider_id": riders,
        "distance_km": dm.distance_km.to_numpy(),
        "promised_minutes": dm.promised.to_numpy(),
        "actual_minutes": np.where(delivered, dm.actual, np.nan),
        "delivered_ts": np.where(delivered, orders.order_ts + pd.to_timedelta(dm.actual, unit="m"), pd.NaT),
        "customer_rating": np.where(delivered & rated, rating, np.nan),
    })
    deliveries["delivered_ts"] = pd.to_datetime(deliveries["delivered_ts"]).dt.floor("s")
    deliveries["customer_rating"] = deliveries["customer_rating"].astype("Int64")
    del st
    return deliveries[delivered].reset_index(drop=True), orders


def _pricing(orders, items, rng):
    tot = (items.unit_price * items.quantity).groupby(items.order_id).sum().rename("item_total")
    orders = orders.merge(tot, left_on="order_id", right_index=True)
    n = len(orders)
    month = orders.order_ts.dt.month.to_numpy()
    coupon = np.full(n, None, dtype=object)
    u = rng.random(n)
    first = orders.is_first.to_numpy() == 1
    coupon[first & (u < 0.7) & (orders.item_total >= 199)] = "WELCOME50"
    rep = ~first
    coupon[rep & (u < 0.12)] = "SAVE10"
    coupon[rep & (u >= 0.12) & (u < 0.20) & np.isin(month, [10, 11]) & (orders.item_total >= 699)] = "FESTIVE100"
    coupon[rep & (u >= 0.20) & (u < 0.24) & (orders.item_total < 199)] = "FREEDEL"
    disc = np.select([coupon == "WELCOME50", coupon == "SAVE10", coupon == "FESTIVE100"],
                     [50, np.minimum(orders.item_total * 0.10, 75), 100], 0.0)
    fee = np.where((orders.item_total >= FREE_DELIVERY_THRESHOLD) | (coupon == "FREEDEL"), 0,
                   np.where(orders.order_ts.dt.hour.isin([23, 0, 1, 2, 3, 4, 5]), 35, 25))
    orders["coupon_code"] = coupon
    orders["discount_amount"] = np.round(disc, 2)
    orders["delivery_fee"] = fee
    orders["order_value"] = np.round(orders.item_total - orders.discount_amount + fee, 2)
    pm = rng.choice(["UPI", "Card", "Cash on Delivery", "Wallet"], n, p=[0.68, 0.10, 0.17, 0.05])
    orders["payment_method"] = pm
    return orders


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--customers", type=int, default=38000)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = simulate(args.seed, args.customers)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"{name:<12} {len(df):>9,} rows")


if __name__ == "__main__":
    main()

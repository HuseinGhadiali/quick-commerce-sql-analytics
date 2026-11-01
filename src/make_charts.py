"""Build README charts from the CSVs written by run_analysis.py."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

from db import ROOT
from viz_style import BLUES, MUTED, SERIES, TEXT, TEXT_2, apply_style, finish

R = ROOT / "results"
IMG = ROOT / "images"


def monthly_gmv():
    df = pd.read_csv(R / "01_monthly_kpis.csv", parse_dates=["month"])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(df.month, df.gmv_lakh, color=SERIES[0], marker="o", markersize=4)
    for label, m in [("Diwali '24", "2024-11-01"), ("Diwali '25", "2025-10-01")]:
        row = df[df.month == m].iloc[0]
        ax.annotate(label, (row.month, row.gmv_lakh), xytext=(0, 10), textcoords="offset points",
                    ha="center", fontsize=9, color=TEXT_2)
    last = df.iloc[-1]
    ax.annotate(f"Rs {last.gmv_lakh:.0f} L", (last.month, last.gmv_lakh), xytext=(6, -4),
                textcoords="offset points", fontsize=9, color=TEXT)
    ax.set_ylabel("Delivered GMV (Rs lakh)")
    ax.set_ylim(0, df.gmv_lakh.max() * 1.15)
    finish(fig, ax, "GMV grew 2.3x in 2025, with festive peaks every October/November",
           "Delivered order value per month, 2024-2025", IMG / "monthly_gmv.png")


def monsoon():
    import duckdb  # noqa: F401  (results already computed; recompute a monthly view for the chart)

    from db import build_database
    con = build_database()
    df = con.sql("""
        SELECT DATE_TRUNC('month', o.order_ts)::date AS month,
               CASE WHEN c.city_name = 'Mumbai' THEN 'Mumbai' ELSE 'Other cities' END AS grp,
               AVG(CASE WHEN d.actual_minutes <= d.promised_minutes THEN 1.0 ELSE 0 END) AS on_time
        FROM deliveries d JOIN orders o USING (order_id)
        JOIN dark_stores s USING (store_id) JOIN cities c USING (city_id)
        GROUP BY ALL ORDER BY 1""").df()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i, (g, sub) in enumerate(df.groupby("grp")):
        ax.plot(sub.month, sub.on_time, color=SERIES[i], label=g)
        ax.annotate(g, (sub.month.iloc[-1], sub.on_time.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color=TEXT)
    for y in (2024, 2025):
        ax.axvspan(pd.Timestamp(f"{y}-06-01"), pd.Timestamp(f"{y}-09-30"), color=BLUES[0], alpha=0.5, lw=0)
        ax.text(pd.Timestamp(f"{y}-07-15"), 0.42, "monsoon", ha="center", fontsize=8.5, color=TEXT_2)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(0.4, 1.0)
    ax.set_ylabel("Delivered within promised time")
    ax.legend(loc="lower left")
    finish(fig, ax, "Mumbai's on-time rate drops ~28 pts every monsoon",
           "Share of orders delivered within the promised 10/15/20 minutes", IMG / "monsoon_sla.png")


def cohort_heatmap():
    df = pd.read_csv(R / "13_cohort_retention.csv", parse_dates=["cohort_month"])
    cols = ["m1_pct", "m2_pct", "m3_pct", "m6_pct", "m12_pct"]
    mat = df[cols].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(7.5, 8))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blues", BLUES)
    cmap.set_bad("#f1f0ec")
    im = ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=cmap, vmin=0, vmax=70)
    ax.set_xticks(range(len(cols)), ["Month 1", "Month 2", "Month 3", "Month 6", "Month 12"])
    ax.set_yticks(range(len(df)), [f"{d:%b %Y} (n={n:,})" for d, n in zip(df.cohort_month, df.cohort_size)])
    ax.grid(False)
    for (i, j), v in np.ndenumerate(mat):
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if v > 40 else TEXT)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("% of cohort ordering in that month", color=TEXT_2)
    cb.outline.set_visible(False)
    finish(fig, ax, "~60% of customers return in month 1, ~20% by month 6",
           "Customers grouped by first-order month", IMG / "cohort_retention.png")


def ratings():
    df = pd.read_csv(R / "25_rating_drivers.csv")
    labels = [s.split(". ", 1)[1] for s in df.delivery_outcome]
    fig, ax = plt.subplots(figsize=(8.5, 4))
    colors = [MUTED, MUTED, MUTED, SERIES[1], SERIES[1]]
    bars = ax.bar(labels, df.one_two_star_pct / 100, color=colors, width=0.55)
    for b, v in zip(bars, df.one_two_star_pct):
        ax.text(b.get_x() + b.get_width() / 2, v / 100 + 0.015, f"{v:.0f}%", ha="center", fontsize=9, color=TEXT)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("Share of 1-2 star ratings")
    finish(fig, ax, "Ratings hold up to 5 min late, then collapse",
           "Share of rated orders scoring 1-2 stars, by delivery outcome", IMG / "rating_vs_lateness.png")


def threshold():
    df = pd.read_csv(R / "21_free_delivery_threshold.csv")
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = [SERIES[0] if v == 199 else MUTED for v in df.cart_value_from]
    ax.bar(df.cart_value_from + 5, df.orders, width=8.6, color=colors)
    ax.axvline(199, color=TEXT_2, lw=1)
    ax.text(197, df.orders.max() * 0.95, "Free delivery from Rs 199", fontsize=9, color=TEXT_2, ha="right")
    ax.set_xlabel("Cart value (Rs, Rs 10 buckets)")
    ax.set_ylabel("Orders (2025)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    finish(fig, ax, "Customers top up their carts to clear the free-delivery threshold",
           "Order count by cart value around Rs 199", IMG / "free_delivery_bunching.png")


def channels():
    df = pd.read_csv(R / "15_channel_quality.csv").sort_values("revenue_per_customer_180d")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(df.acquisition_channel, df.revenue_per_customer_180d, color=SERIES[0], height=0.55)
    for y, (v, r) in enumerate(zip(df.revenue_per_customer_180d, df.repeat_90d_pct)):
        ax.text(v + 80, y, f"Rs {v:,.0f}  ·  {r:.0f}% repeat in 90d", va="center", fontsize=9, color=TEXT)
    ax.set_xlim(0, df.revenue_per_customer_180d.max() * 1.45)
    ax.set_xlabel("Revenue per customer in first 180 days (Rs)")
    ax.grid(axis="y", visible=False)
    finish(fig, ax, "Referral customers are worth 2.6x Paid Social customers",
           "Customers who signed up before Jul-2025", IMG / "channel_quality.png")


if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    apply_style()
    for f in (monthly_gmv, monsoon, cohort_heatmap, ratings, threshold, channels):
        f()
        print("chart:", f.__name__)

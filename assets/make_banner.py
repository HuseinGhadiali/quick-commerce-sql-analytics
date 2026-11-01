"""Render assets/banner.png from the project data (python assets/make_banner.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from banner import glow_line, glow_scatter, make_banner  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
import duckdb
# ---------- quick commerce: every dot is a delivery (time of day x minutes taken) ----------
con = duckdb.connect()
qc = con.sql(f"""SELECT EXTRACT(HOUR FROM o.order_ts) + EXTRACT(MINUTE FROM o.order_ts)/60.0 AS t, d.actual_minutes AS m,
                       o.store_id < 109 AS mumbai
                FROM read_csv('{ROOT}/data/raw/deliveries.csv') d
                JOIN read_csv('{ROOT}/data/raw/orders.csv') o USING (order_id)
                USING SAMPLE 9000 (reservoir, 7)""").df()
vol = con.sql(f"""SELECT EXTRACT(HOUR FROM order_ts) h, COUNT(*) n FROM read_csv('{ROOT}/data/raw/orders.csv') GROUP BY 1 ORDER BY 1""").df()

def qc_art(ax, acc):
    ax.set_xlim(-1, 25); ax.set_ylim(-2, 34)
    jitter = np.random.default_rng(1).normal(0, 0.12, len(qc))
    glow_scatter(ax, qc.t[~qc.mumbai] + jitter[~qc.mumbai], qc.m[~qc.mumbai], acc[1], s=3, alpha=0.55)
    glow_scatter(ax, qc.t[qc.mumbai] + jitter[qc.mumbai], qc.m[qc.mumbai], acc[0], s=3, alpha=0.7)
    from scipy.interpolate import make_interp_spline
    xs = np.linspace(0, 23, 300); ys = make_interp_spline(vol.h, vol.n / vol.n.max() * 9 + 22, k=3)(xs)
    glow_line(ax, xs, ys, acc[2], lw=2.5)
    ax.text(23.4, ys[-1], "orders\nby hour", color=acc[2], fontsize=9, va="center", alpha=0.9)
    ax.text(0.2, 1.0, "each dot = one delivery  ·  minutes taken vs time of day", color="white", alpha=0.55, fontsize=9)

make_banner(f"{ROOT}/assets/banner.png",
            "Quick-Commerce SQL Analytics", "25 business questions · 451K orders · 8 Indian cities · 10-minute delivery",
            ["PostgreSQL", "DuckDB", "Window functions", "Cohorts & RFM"], qc_art, theme="sunset",
            emoji_free_kicker="SQL case study")


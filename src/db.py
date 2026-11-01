"""Load the generated CSVs into a DuckDB database using the PostgreSQL-compatible schema."""
from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["cities", "dark_stores", "customers", "products", "orders", "order_items", "deliveries"]


def build_database(raw_dir: Path = ROOT / "data" / "raw", db_path: Path | str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(db_path))
    con.sql((ROOT / "sql" / "00_schema.sql").read_text())
    for t in TABLES:
        con.sql(f"INSERT INTO {t} SELECT * FROM read_csv('{(raw_dir / f'{t}.csv').as_posix()}', header = true)")
    return con

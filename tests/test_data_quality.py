import re

import pytest
from conftest import ROOT

CHECKS = re.findall(r"-- name: (\w+)\n(.*?;)", (ROOT / "sql" / "01_data_quality_checks.sql").read_text(), re.S)


@pytest.mark.parametrize("name,sql", CHECKS, ids=[c[0] for c in CHECKS])
def test_no_violations(con, name, sql):
    violations = con.sql(sql).fetchall()[0][0]
    assert violations == 0, f"{name}: {violations} violating rows"


def test_primary_keys_unique(con):
    for table, key in [("orders", "order_id"), ("customers", "customer_id"), ("products", "product_id"),
                       ("deliveries", "order_id"), ("order_items", "order_id, product_id")]:
        dupes = con.sql(f"SELECT COUNT(*) FROM (SELECT {key} FROM {table} GROUP BY {key} HAVING COUNT(*) > 1)").fetchall()[0][0]
        assert dupes == 0, table

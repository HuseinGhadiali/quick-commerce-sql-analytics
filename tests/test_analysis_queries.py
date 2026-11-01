import pytest
from conftest import ROOT

QUERIES = sorted((ROOT / "sql" / "analysis").glob("*.sql"))


@pytest.mark.parametrize("path", QUERIES, ids=[p.stem for p in QUERIES])
def test_query_runs_and_returns_rows(con, path):
    df = con.sql(path.read_text()).df()
    assert len(df) > 0
    assert not df.columns.duplicated().any()


def test_every_query_documents_question_and_skills():
    for path in QUERIES:
        text = path.read_text()
        assert text.startswith(f"-- Q{path.stem[:2]}."), path.name
        assert "-- Skills:" in text, path.name


def test_rfm_segments_cover_all_customers(con):
    df = con.sql((ROOT / "sql" / "analysis" / "14_rfm_segments.sql").read_text()).df()
    buyers = con.sql("SELECT COUNT(DISTINCT customer_id) FROM orders WHERE order_status = 'Delivered'").fetchall()[0][0]
    assert df.customers.sum() == buyers
    assert abs(df.revenue_pct.sum() - 100) < 0.5


def test_market_basket_lift_is_consistent(con):
    sql = (ROOT / "sql" / "analysis" / "20_market_basket.sql").read_text().replace(">= 300", ">= 20")
    df = con.sql(sql).df()
    assert (df.lift > 0).all()
    assert (df.confidence_a_to_b_pct <= 100).all()

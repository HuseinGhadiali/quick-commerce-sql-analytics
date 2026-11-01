import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from db import build_database  # noqa: E402
from generate_data import simulate  # noqa: E402


@pytest.fixture(scope="session")
def con(tmp_path_factory):
    """A small (2,000-customer) copy of the dataset so the suite runs in seconds."""
    raw = tmp_path_factory.mktemp("raw")
    for name, df in simulate(seed=7, n_customers=2000).items():
        df.to_csv(raw / f"{name}.csv", index=False)
    return build_database(raw)

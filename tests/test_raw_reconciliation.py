"""
Reconciliation against raw Olist extracts when present.
Skips cleanly in code-only / sample mode.
"""
import pytest
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "olist"
PROCESSED = ROOT / "data" / "processed"


def _raw_available():
    needed = ["olist_order_items_dataset.csv", "olist_orders_dataset.csv"]
    return all((RAW / f).exists() for f in needed)


@pytest.fixture(scope="module")
def raw_items():
    if not _raw_available():
        pytest.skip("raw Olist not present")
    return pd.read_csv(RAW / "olist_order_items_dataset.csv")


@pytest.fixture(scope="module")
def order_line():
    path = PROCESSED / "order_line_finance.csv"
    if not path.exists() or path.stat().st_size < 1000:
        path2 = PROCESSED / "order_line.csv"
        if not path2.exists():
            pytest.skip("processed order line not present")
        return pd.read_csv(path2, low_memory=False)
    return pd.read_csv(path, low_memory=False)


def test_item_row_count_equals_raw(raw_items, order_line):
    assert len(order_line) == len(raw_items), (
        f"order_line {len(order_line)} != raw items {len(raw_items)}"
    )


def test_price_sum_matches_raw(raw_items, order_line):
    raw_price = float(raw_items["price"].sum())
    if "price" in order_line.columns:
        proc = float(order_line["price"].sum())
    elif "gross_sales" in order_line.columns:
        proc = float(order_line["gross_sales"].sum())
    else:
        pytest.skip("no price/gross column")
    assert abs(proc - raw_price) < 1.0, f"price sum diff {proc - raw_price}"


def test_freight_sum_matches_raw(raw_items, order_line):
    raw_f = float(raw_items["freight_value"].sum())
    if "freight_value" not in order_line.columns:
        pytest.skip("no freight column")
    proc = float(order_line["freight_value"].sum())
    assert abs(proc - raw_f) < 1.0, f"freight sum diff {proc - raw_f}"

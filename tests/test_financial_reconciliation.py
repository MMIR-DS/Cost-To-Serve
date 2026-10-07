"""
Financial reconciliation tests.
Falls back to data/sample when full processed files are absent.
"""

import pytest
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"


def _load_order_line():
    full = PROCESSED / "order_line_finance.csv"
    sample = SAMPLE / "order_line_finance_sample.csv"
    if full.exists() and full.stat().st_size > 1000:
        return pd.read_csv(full, low_memory=False)
    assert sample.exists(), "Run finance pipeline or use sample data"
    return pd.read_csv(sample, low_memory=False)


def _load_customer_month():
    full = PROCESSED / "customer_month.csv"
    sample = SAMPLE / "customer_month_sample.csv"
    if full.exists() and full.stat().st_size > 1000:
        return pd.read_csv(full)
    assert sample.exists()
    return pd.read_csv(sample)


@pytest.fixture(scope="module")
def order_line():
    return _load_order_line()


@pytest.fixture(scope="module")
def customer_month():
    return _load_customer_month()


def test_no_negative_gross_sales(order_line):
    assert (order_line["gross_sales"] >= 0).all()


def test_net_sales_le_gross(order_line):
    assert (order_line["net_sales"] <= order_line["gross_sales"] + 1e-6).all()


def test_canceled_have_zero_net(order_line):
    if "is_canceled" not in order_line.columns:
        pytest.skip("is_canceled not in sample")
    canceled = order_line[order_line["is_canceled"]]
    if len(canceled) == 0:
        pytest.skip("No canceled rows in this sample")
    assert (canceled["net_sales"] == 0).all()
    assert (canceled["product_contribution"] == 0).all()


def test_product_contribution_identity(order_line):
    calc = order_line["net_sales"] - order_line["product_variable_cost"]
    assert (abs(order_line["product_contribution"] - calc) < 1e-6).all()


def test_product_cost_pct_consistent(order_line):
    assert order_line["product_cost_pct_used"].nunique() == 1
    pct = order_line["product_cost_pct_used"].iloc[0]
    assert 0.20 <= pct <= 0.50


def test_no_duplicate_order_item(order_line):
    assert not order_line.duplicated(subset=["order_id", "order_item_id"]).any()


def test_customer_month_grain(customer_month):
    assert not customer_month.duplicated(
        subset=["customer_unique_id", "purchase_year_month"]
    ).any()


def test_positive_product_contribution_exists(order_line):
    assert (order_line["product_contribution"] > 0).any()


def test_customer_month_reconciliation(order_line, customer_month):
    if len(order_line) < 1000 or len(customer_month) < 500:
        pytest.skip("Sample mode — skip strict full reconciliation")
    ol_net = order_line["net_sales"].sum()
    cm_net = customer_month["net_sales"].sum()
    assert abs(ol_net - cm_net) < 1.0

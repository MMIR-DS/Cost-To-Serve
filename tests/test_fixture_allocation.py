"""Deterministic fixture tests for allocation and pass-through."""
import pytest
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "tiny_order_lines.csv"


@pytest.fixture(scope="module")
def tiny():
    assert FIXTURE.exists()
    return pd.read_csv(FIXTURE)


def test_tiny_fixture_has_canceled_and_active(tiny):
    assert tiny["is_canceled"].any()
    assert (~tiny["is_canceled"]).any()


def test_pass_through_returns_rate_on_fixture():
    from src.cost_to_serve.economic_robustness import pass_through_contrib
    import src.cost_to_serve.economic_robustness as er
    cm = pd.DataFrame({
        "n_order_lines": [2, 0, 1],
        "n_canceled_lines": [1, 5, 0],
        "net_sales": [100.0, 0.0, 50.0],
        "product_contribution": [65.0, 0.0, 32.5],
        "n_orders": [1, 0, 1],
        "total_weight_g": [1000.0, 0.0, 500.0],
    })
    old = er.POOL_COSTS.copy()
    er.POOL_COSTS = {
        "order_handling": 0.0,
        "distribution": 0.0,
        "warehousing": 0.0,
        "returns_waste": 60.0,
    }
    try:
        c = pass_through_contrib(cm, include_returns=True)
        assert abs(c.iloc[0] - 55.0) < 1e-6
        assert abs(c.iloc[1] - (-50.0)) < 1e-6
        assert abs(c.iloc[2] - 32.5) < 1e-6
    finally:
        er.POOL_COSTS = old


def test_passthrough_formula_on_fixture(tiny):
    from src.cost_to_serve.rates import compute_order_table
    ot = compute_order_table(tiny)
    expected = ot["product_contribution"] - ot["cost_oh"] - ot["cost_wh"]
    assert (ot["contrib_passthrough"] - expected).abs().max() < 1e-6


def test_mixed_customer_has_active_and_canceled(tiny):
    c3 = tiny[tiny["customer_unique_id"] == "c3"]
    if len(c3) == 0:
        pytest.skip("c3 not in fixture")
    assert c3["is_canceled"].any() and (~c3["is_canceled"]).any()


def test_binding_returns_via_pass_through_contrib_diff():
    from src.cost_to_serve.economic_robustness import pass_through_contrib
    import src.cost_to_serve.economic_robustness as er
    old = er.POOL_COSTS.copy()
    er.POOL_COSTS = {
        "order_handling": 0.0,
        "distribution": 0.0,
        "warehousing": 0.0,
        "returns_waste": 60.0,
    }
    try:
        cm = pd.DataFrame({
            "n_order_lines": [2, 0, 1],
            "n_canceled_lines": [1, 5, 0],
            "net_sales": [100.0, 0.0, 50.0],
            "product_contribution": [65.0, 0.0, 32.5],
            "n_orders": [1, 0, 1],
            "total_weight_g": [1000.0, 0.0, 500.0],
        })
        rate = 60.0 / 6.0
        c0 = pass_through_contrib(cm, include_returns=False)
        c1 = pass_through_contrib(cm, include_returns=True)
        diff = c0 - c1
        assert abs(diff.iloc[0] - rate * 1) < 1e-6
        assert abs(diff.iloc[1] - rate * 5) < 1e-6
        assert abs(diff.iloc[2] - 0.0) < 1e-6
    finally:
        er.POOL_COSTS = old

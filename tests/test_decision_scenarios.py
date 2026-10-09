import pandas as pd
import pytest

from src.scenarios.decision_scenarios import run_commercial_scenarios


@pytest.fixture
def baseline_customer_months():
    # Small deterministic fixture: values are illustrative, not Olist results.
    return pd.DataFrame(
        {
            "net_sales": [100.0, 200.0],
            "product_variable_cost": [35.0, 70.0],
            "product_contribution": [65.0, 130.0],
            "cost_to_serve": [10.0, 20.0],
            "customer_contribution": [55.0, 110.0],
        }
    )


def _scenario(results, name):
    return results.loc[results["scenario"] == name].iloc[0]


def test_price_up_5pct_applies_sales_multiplier_once(baseline_customer_months):
    results = run_commercial_scenarios(baseline_customer_months)
    price_up = _scenario(results, "price_up_5pct")

    baseline_sales = baseline_customer_months["net_sales"].sum()
    assert price_up["total_net_sales"] == pytest.approx(baseline_sales * 1.05)
    assert price_up["net_sales_multiplier"] == pytest.approx(1.05)


def test_price_up_5pct_holds_absolute_product_cost_fixed(baseline_customer_months):
    results = run_commercial_scenarios(baseline_customer_months)
    price_up = _scenario(results, "price_up_5pct")

    baseline_cost = baseline_customer_months["product_variable_cost"].sum()
    expected_contribution = (
        baseline_customer_months["net_sales"].sum() * 1.05 - baseline_cost
    )
    assert price_up["total_product_contribution"] == pytest.approx(
        expected_contribution
    )


def test_commercial_scenarios_keep_service_cost_fixed(baseline_customer_months):
    results = run_commercial_scenarios(baseline_customer_months)
    expected_cts = baseline_customer_months["cost_to_serve"].sum()

    assert all(
        value == pytest.approx(expected_cts) for value in results["total_cts"]
    )


@pytest.mark.parametrize(
    ("scenario", "multiplier"),
    [
        ("baseline", 1.00),
        ("discount_reduction", 1.03),
        ("price_down_pressure", 0.96),
    ],
)
def test_other_commercial_scenarios_apply_declared_sales_multiplier(
    baseline_customer_months, scenario, multiplier
):
    results = run_commercial_scenarios(baseline_customer_months)
    row = _scenario(results, scenario)

    assert row["total_net_sales"] == pytest.approx(
        baseline_customer_months["net_sales"].sum() * multiplier
    )

"""
Consistency tests for robustness & scenario outputs.
Skips gracefully when summary JSONs are absent (code-only checkout).
"""

import pytest
import json
from pathlib import Path

OUTPUTS = Path(__file__).resolve().parents[1] / "outputs"


@pytest.fixture(scope="module")
def robustness():
    path = OUTPUTS / "robustness_summary.json"
    if not path.exists():
        pytest.skip("robustness_summary.json not present — run robustness engine")
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def scenarios():
    path = OUTPUTS / "scenarios_summary.json"
    if not path.exists():
        pytest.skip("scenarios_summary.json not present — run scenarios module")
    with open(path) as f:
        return json.load(f)


def test_robustness_summary_structure(robustness):
    assert "product_cost" in robustness
    assert "pool_size" in robustness
    assert "operating_regimes" in robustness
    assert "stability" in robustness


def test_sign_stability_high(robustness):
    for name, val in robustness["stability"]["sign_stability"].items():
        assert val > 0.95, f"{name} sign stability too low: {val}"


def test_rank_correlation_high(robustness):
    for name, val in robustness["stability"]["rank_correlation"].items():
        assert val > 0.95, f"{name} rank corr too low: {val}"


def test_scenarios_structure(scenarios):
    assert "commercial" in scenarios
    assert "service_model" in scenarios


def test_commercial_baseline_delta_zero(scenarios):
    baseline = next(s for s in scenarios["commercial"] if s["scenario"] == "baseline")
    assert abs(baseline["delta_customer_contribution"]) < 1.0


def test_service_baseline_delta_zero(scenarios):
    baseline = next(s for s in scenarios["service_model"] if s["scenario"] == "baseline")
    assert abs(baseline["delta_customer_contribution"]) < 1.0
    assert abs(baseline["delta_cts"]) < 1.0

"""
Robustness Engine — Customer Contribution After Cost-to-Serve

Tests whether customer conclusions remain stable under plausible changes in:
  1. Product variable cost %
  2. Cost-pool sizes
  3. Alternative drivers
  4. Operating regimes
  5. Combined COGS × pool corners

Illustrative stress regimes (e.g. freight ×1.40) are Modeled scenario multipliers,
not estimated operating probabilities.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import json
from copy import deepcopy

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

from src.cost_to_serve.pools_and_allocation import COST_POOLS, allocate_pool
from src.cost_to_serve.config import PRODUCT_COST_BASELINE, PRODUCT_COST_RANGE

PRODUCT_COST_SCENARIOS = {"low": PRODUCT_COST_RANGE[0], "baseline": PRODUCT_COST_BASELINE, "high": PRODUCT_COST_RANGE[1]}

POOL_SIZE_SCENARIOS = {
    "baseline": {k: 1.0 for k in COST_POOLS},
    "cost_pressure": {k: 1.20 for k in COST_POOLS},
    "cost_relief": {k: 0.85 for k in COST_POOLS},
}

ALTERNATIVE_DRIVERS = {
    "distribution": "total_weight_g",
    "warehousing": "total_volume_cm3",
    "order_handling": "n_orders",
}

OPERATING_REGIMES = {
    "standard": {
        "description": "Normal operating conditions",
        "pool_multipliers": {k: 1.0 for k in COST_POOLS},
        "driver_overrides": {},
    },
    "freight_heavy": {
        "description": "Transportation more demanding",
        "pool_multipliers": {
            "order_handling": 1.0,
            "distribution": 1.40,
            "warehousing": 1.0,
            "returns_waste": 1.0,
        },
        "driver_overrides": {},
    },
    "handling_heavy": {
        "description": "Order complexity / handling intensity up",
        "pool_multipliers": {
            "order_handling": 1.30,
            "distribution": 1.0,
            "warehousing": 1.15,
            "returns_waste": 1.0,
        },
        "driver_overrides": {},
    },
    "high_return": {
        "description": "Elevated non-fulfillment / returns pressure",
        "pool_multipliers": {
            "order_handling": 1.0,
            "distribution": 1.0,
            "warehousing": 1.0,
            "returns_waste": 1.50,
        },
        "driver_overrides": {},
    },
}


def _recompute_product(cm: pd.DataFrame, product_cost_pct: float) -> pd.DataFrame:
    cm = cm.copy()
    cm["product_variable_cost"] = cm["net_sales"] * product_cost_pct
    cm["product_contribution"] = cm["net_sales"] - cm["product_variable_cost"]
    return cm


def _allocate_all_pools(cm: pd.DataFrame, pool_defs: dict) -> pd.DataFrame:
    cm = cm.copy()
    for pool_key, meta in pool_defs.items():
        driver = meta.get("primary_driver", COST_POOLS[pool_key]["primary_driver"])
        if driver not in cm.columns:
            driver = COST_POOLS[pool_key]["primary_driver"]
        d = cm[driver].fillna(0).clip(lower=0)
        tot = d.sum()
        rate = meta["pool_cost"] / tot if tot > 0 else 0.0
        cm[f"cost_{pool_key}"] = d * rate
    cost_cols = [f"cost_{k}" for k in COST_POOLS]
    cm["cost_to_serve"] = cm[cost_cols].sum(axis=1)
    cm["customer_contribution"] = cm["product_contribution"] - cm["cost_to_serve"]
    return cm


def _summary(cm: pd.DataFrame, scenario_type: str, scenario: str, **extra) -> dict:
    return {
        "scenario_type": scenario_type,
        "scenario": scenario,
        "total_customer_contribution": float(cm["customer_contribution"].sum()),
        "n_positive": int((cm["customer_contribution"] > 0).sum()),
        "n_negative": int((cm["customer_contribution"] < 0).sum()),
        **extra,
    }


def run_product_cost_robustness(base_cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, pct in PRODUCT_COST_SCENARIOS.items():
        cm = _recompute_product(base_cm, pct)
        pool_defs = deepcopy(COST_POOLS)
        cm = _allocate_all_pools(cm, pool_defs)
        rows.append(_summary(cm, "product_cost", label, product_cost_pct=pct))
    return pd.DataFrame(rows)


def run_pool_size_robustness(base_cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, mults in POOL_SIZE_SCENARIOS.items():
        cm = base_cm.copy()
        pool_defs = deepcopy(COST_POOLS)
        for k in pool_defs:
            pool_defs[k]["pool_cost"] = COST_POOLS[k]["pool_cost"] * mults[k]
        cm = _allocate_all_pools(cm, pool_defs)
        rows.append(_summary(cm, "pool_size", label))
    return pd.DataFrame(rows)


def run_driver_robustness(base_cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Primary drivers
    cm = _allocate_all_pools(base_cm.copy(), deepcopy(COST_POOLS))
    rows.append(_summary(cm, "driver", "primary"))
    # Alternative drivers where available
    pool_defs = deepcopy(COST_POOLS)
    for pool, alt in ALTERNATIVE_DRIVERS.items():
        if alt in base_cm.columns:
            pool_defs[pool]["primary_driver"] = alt
    cm = _allocate_all_pools(base_cm.copy(), pool_defs)
    rows.append(_summary(cm, "driver", "alternative"))
    return pd.DataFrame(rows)


def run_operating_regimes(base_cm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, reg in OPERATING_REGIMES.items():
        cm = base_cm.copy()
        pool_defs = deepcopy(COST_POOLS)
        for k, m in reg["pool_multipliers"].items():
            pool_defs[k]["pool_cost"] = COST_POOLS[k]["pool_cost"] * m
        cm = _allocate_all_pools(cm, pool_defs)
        rows.append(_summary(cm, "operating_regime", label, description=reg["description"]))
    return pd.DataFrame(rows)


def run_combined_corners(base_cm: pd.DataFrame) -> pd.DataFrame:
    corners = {
        "best": (0.25, 0.85),
        "baseline": (0.35, 1.0),
        "worst": (0.45, 1.20),
    }
    rows = []
    for label, (cogs, pool_mult) in corners.items():
        cm = _recompute_product(base_cm, cogs)
        pool_defs = deepcopy(COST_POOLS)
        for k in pool_defs:
            pool_defs[k]["pool_cost"] = COST_POOLS[k]["pool_cost"] * pool_mult
        cm = _allocate_all_pools(cm, pool_defs)
        rows.append(
            _summary(
                cm,
                "combined_corner",
                label,
                product_cost_pct=cogs,
                pool_multiplier=pool_mult,
            )
        )
    return pd.DataFrame(rows)


def _rank_corr(a: pd.Series, b: pd.Series) -> float:
    """Spearman correlation without a scipy dependency."""
    ar = a.rank(method="average")
    br = b.rank(method="average")
    corr = ar.corr(br)
    return float(corr) if pd.notna(corr) else 1.0


def _scenario_series(base_cm: pd.DataFrame) -> dict[str, pd.Series]:
    series = {}
    for label, pct in PRODUCT_COST_SCENARIOS.items():
        cm = _allocate_all_pools(
            _recompute_product(base_cm, pct), deepcopy(COST_POOLS)
        )
        series[f"prodcost_{label}"] = cm["customer_contribution"]

    for label, mults in POOL_SIZE_SCENARIOS.items():
        pool_defs = deepcopy(COST_POOLS)
        for k in pool_defs:
            pool_defs[k]["pool_cost"] = COST_POOLS[k]["pool_cost"] * mults[k]
        series[f"pool_{label}"] = _allocate_all_pools(
            base_cm.copy(), pool_defs
        )["customer_contribution"]

    for label, reg in OPERATING_REGIMES.items():
        pool_defs = deepcopy(COST_POOLS)
        for k, m in reg["pool_multipliers"].items():
            pool_defs[k]["pool_cost"] = COST_POOLS[k]["pool_cost"] * m
        series[f"regime_{label}"] = _allocate_all_pools(
            base_cm.copy(), pool_defs
        )["customer_contribution"]
    return series


def compute_sign_and_rank_stability(base_cm: pd.DataFrame) -> dict:
    """Compare each robustness scenario with the baseline contribution vector."""
    series = _scenario_series(base_cm)
    base = series["prodcost_baseline"]
    base_sign = np.sign(base.to_numpy())

    sign_stability = {}
    rank_correlation = {}
    for name, values in series.items():
        signs = np.sign(values.to_numpy())
        sign_stability[name] = float((signs == base_sign).mean())
        rank_correlation[name] = _rank_corr(base, values)

    all_same = np.ones(len(base), dtype=bool)
    for values in series.values():
        all_same &= np.sign(values.to_numpy()) == base_sign

    return {
        "n_customer_months": int(len(base)),
        "sign_stable_share": float(all_same.mean()),
        "scenarios_compared": list(series.keys()),
        "sign_stability": sign_stability,
        "rank_correlation": rank_correlation,
        "note": (
            "Full-CM sign stability is dominated by the large positive mass; "
            "prefer economic-only robust classes."
        ),
    }

def run_full_robustness():
    print("Loading baseline Customer × Month CTS …")
    cts_path = PROCESSED / "customer_month_cts.csv"
    if not cts_path.exists():
        raise FileNotFoundError("Run pools_and_allocation.py first")
    base_cm = pd.read_csv(cts_path)
    print(f"  {len(base_cm):,} rows")

    print("\n1. Product-cost robustness …")
    pc = run_product_cost_robustness(base_cm)
    print(pc.to_string(index=False))

    print("\n2. Pool-size robustness …")
    ps = run_pool_size_robustness(base_cm)
    print(ps.to_string(index=False))

    print("\n3. Driver robustness …")
    dr = run_driver_robustness(base_cm)
    print(dr.to_string(index=False))

    print("\n4. Operating regimes …")
    reg = run_operating_regimes(base_cm)
    print(reg.to_string(index=False))

    print("\n5. Combined corners …")
    corners = run_combined_corners(base_cm)
    print(corners.to_string(index=False))

    print("\n6. Sign & Rank stability …")
    stability = compute_sign_and_rank_stability(base_cm)
    print(json.dumps(stability, indent=2))

    summary = {
        "product_cost": pc.to_dict(orient="records"),
        "pool_size": ps.to_dict(orient="records"),
        "driver": dr.to_dict(orient="records"),
        "operating_regimes": reg.to_dict(orient="records"),
        "combined_corners": corners.to_dict(orient="records"),
        "stability": stability,
    }
    with open(OUTPUTS / "robustness_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nRobustness summary written to {OUTPUTS / 'robustness_summary.json'}")
    return summary


if __name__ == "__main__":
    run_full_robustness()

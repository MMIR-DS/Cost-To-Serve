"""
Decision Scenarios — Customer Contribution After Cost-to-Serve

Two families only:
  A. Commercial Terms  (price, discount levers — illustrative)
  B. Service Model     (delivery frequency / service intensity)

NOTE: Commercial/service scenarios are *illustrative arithmetic* on Modeled baselines.
Prefer key_findings + tipping grid for claims.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import json

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

from src.cost_to_serve.pools_and_allocation import COST_POOLS, allocate_pool

COMMERCIAL_SCENARIOS = {
    "baseline": {
        "description": "No change",
        "net_sales_multiplier": 1.00,
        "product_cost_pct": 0.35,
    },
    "price_up_5pct": {
        "description": "Price +5% with product variable cost held fixed in BRL (not re-rated on new sales)",
        "net_sales_multiplier": 1.05,
        "product_cost_pct": 0.35,
        "hold_product_cost_absolute": True,
    },
    "discount_reduction": {
        "description": "Effective net sales improvement of 3% via lower discounts/rebates",
        "net_sales_multiplier": 1.03,
        "product_cost_pct": 0.35,
    },
    "price_down_pressure": {
        "description": "Competitive price pressure: net sales -4%",
        "net_sales_multiplier": 0.96,
        "product_cost_pct": 0.35,
    },
}

SERVICE_SCENARIOS = {
    "baseline": {
        "description": "Current service model",
        "cts_multipliers": {k: 1.0 for k in COST_POOLS},
    },
    "lean_delivery": {
        "description": "Reduce delivery frequency / consolidate shipments → Distribution -20%, Order Handling -10%",
        "cts_multipliers": {
            "order_handling": 0.90,
            "distribution": 0.80,
            "warehousing": 1.00,
            "returns_waste": 1.00,
        },
    },
    "premium_service": {
        "description": "Higher service intensity → Distribution +25%, Order Handling +15%",
        "cts_multipliers": {
            "order_handling": 1.15,
            "distribution": 1.25,
            "warehousing": 1.00,
            "returns_waste": 1.00,
        },
    },
    "returns_tightening": {
        "description": "Tighter return policy → Returns & Waste -40%",
        "cts_multipliers": {
            "order_handling": 1.00,
            "distribution": 1.00,
            "warehousing": 1.00,
            "returns_waste": 0.60,
        },
    },
}


def _load_base() -> pd.DataFrame:
    path = PROCESSED / "customer_month_cts.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _allocate_with_scaled_pools(cm: pd.DataFrame, multipliers: dict) -> pd.DataFrame:
    cm = cm.copy()
    for pool_key, mult in multipliers.items():
        driver = COST_POOLS[pool_key]["primary_driver"]
        # Scale existing allocated cost columns if present
        col = f"cost_{pool_key}"
        if col in cm.columns:
            cm[col] = cm[col] * mult
        else:
            cm, _ = allocate_pool(cm, pool_key, driver_col=driver)
            cm[col] = cm[col] * mult
    cost_cols = [f"cost_{k}" for k in COST_POOLS]
    cm["cost_to_serve"] = cm[cost_cols].sum(axis=1)
    cm["customer_contribution"] = cm["product_contribution"] - cm["cost_to_serve"]
    cm["service_cost_headroom"] = cm["product_contribution"] - cm["cost_to_serve"]
    return cm


def run_commercial_scenarios(base_cm: pd.DataFrame) -> pd.DataFrame:
    results = []
    for label, sc in COMMERCIAL_SCENARIOS.items():
        cm = base_cm.copy()
        mult = sc["net_sales_multiplier"]
        if sc.get("hold_product_cost_absolute"):
            # Price up: scale net sales; keep product variable cost fixed in BRL
            old_pvc = cm["product_variable_cost"].copy()
            cm["net_sales"] = cm["net_sales"] * mult
            cm["product_variable_cost"] = old_pvc
            cm["product_contribution"] = cm["net_sales"] - cm["product_variable_cost"]
        else:
            cm["net_sales"] = cm["net_sales"] * mult
            pct = sc["product_cost_pct"]
            cm["product_variable_cost"] = cm["net_sales"] * pct
            cm["product_contribution"] = cm["net_sales"] - cm["product_variable_cost"]
        cm["customer_contribution"] = cm["product_contribution"] - cm["cost_to_serve"]
        summary = {
            "family": "commercial",
            "scenario": label,
            "description": sc["description"],
            "net_sales_multiplier": mult,
            "total_net_sales": float(cm["net_sales"].sum()),
            "total_product_contribution": float(cm["product_contribution"].sum()),
            "total_cts": float(cm["cost_to_serve"].sum()),
            "total_customer_contribution": float(cm["customer_contribution"].sum()),
            "delta_customer_contribution": float(
                cm["customer_contribution"].sum() - base_cm["customer_contribution"].sum()
            ),
            "n_positive": int((cm["customer_contribution"] > 0).sum()),
            "n_negative": int((cm["customer_contribution"] < 0).sum()),
        }
        results.append(summary)
    return pd.DataFrame(results)


def run_service_scenarios(base_cm: pd.DataFrame) -> pd.DataFrame:
    results = []
    for label, sc in SERVICE_SCENARIOS.items():
        cm = base_cm.copy()
        cm = _allocate_with_scaled_pools(cm, sc["cts_multipliers"])
        summary = {
            "family": "service_model",
            "scenario": label,
            "description": sc["description"],
            "total_product_contribution": float(cm["product_contribution"].sum()),
            "total_cts": float(cm["cost_to_serve"].sum()),
            "total_customer_contribution": float(cm["customer_contribution"].sum()),
            "delta_customer_contribution": float(
                cm["customer_contribution"].sum() - base_cm["customer_contribution"].sum()
            ),
            "delta_cts": float(cm["cost_to_serve"].sum() - base_cm["cost_to_serve"].sum()),
            "n_positive": int((cm["customer_contribution"] > 0).sum()),
            "n_negative": int((cm["customer_contribution"] < 0).sum()),
        }
        results.append(summary)
    return pd.DataFrame(results)


def run_all_scenarios():
    print("Loading baseline …")
    base = _load_base()
    print(f"  {len(base):,} customer-months")

    print("\n=== COMMERCIAL TERMS SCENARIOS ===")
    comm = run_commercial_scenarios(base)
    print(comm.to_string(index=False))

    print("\n=== SERVICE MODEL SCENARIOS ===")
    serv = run_service_scenarios(base)
    print(serv.to_string(index=False))

    combined = {
        "commercial": comm.to_dict(orient="records"),
        "service_model": serv.to_dict(orient="records"),
    }
    with open(OUTPUTS / "scenarios_summary.json", "w") as f:
        json.dump(combined, f, indent=2, default=str)

    print(f"\nScenarios summary → {OUTPUTS / 'scenarios_summary.json'}")
    return combined


if __name__ == "__main__":
    run_all_scenarios()

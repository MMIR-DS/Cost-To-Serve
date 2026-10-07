"""
Cost-to-Serve V1
Four cost pools → drivers → allocation → Customer Contribution

All pool sizes and rates are Modeled (Tier 3).
Drivers are primarily Observed or Derived (Tier 1/2).
"""

from pathlib import Path
import pandas as pd
import numpy as np
import json

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

from src.cost_to_serve.config import COST_POOLS, PRODUCT_COST_BASELINE, POOL_COSTS, check_cts_share


def load_customer_month() -> pd.DataFrame:
    path = PROCESSED / "customer_month.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run product_contribution first.")
    return pd.read_csv(path)


def allocate_pool(cm: pd.DataFrame, pool_key: str, driver_col: str = None) -> pd.DataFrame:
    """
    Standard proportional allocation:
    Customer Allocated Cost = Pool Cost × (Customer Driver / Total Driver)
    """
    pool = COST_POOLS[pool_key]
    if driver_col is None:
        driver_col = pool["primary_driver"]

    if driver_col not in cm.columns:
        raise KeyError(f"Driver column '{driver_col}' not found in customer_month")

    driver = cm[driver_col].fillna(0).clip(lower=0)
    total_driver = driver.sum()

    if total_driver <= 0:
        allocated = np.zeros(len(cm))
        coverage = 0.0
    else:
        allocated = pool["pool_cost"] * (driver / total_driver)
        coverage = 1.0

    col_name = f"cost_{pool_key}"
    cm = cm.copy()
    cm[col_name] = allocated
    cm[f"driver_{pool_key}"] = driver

    return cm, {
        "pool": pool_key,
        "driver_used": driver_col,
        "pool_cost": pool["pool_cost"],
        "total_driver": float(total_driver),
        "allocated_sum": float(allocated.sum()),
        "coverage": coverage,
        "unallocated": pool["pool_cost"] - float(allocated.sum()),
    }


def run_cost_to_serve(use_alternative_drivers: dict = None):
    """
    Main entry: allocate all four pools and compute Customer Contribution.
    use_alternative_drivers: optional dict {pool_key: driver_col} for robustness testing.
    """
    print("Loading Customer × Month …")
    cm = load_customer_month()
    print(f"  {len(cm):,} customer-months")

    reconciliations = []
    for pool_key in COST_POOLS:
        alt = (use_alternative_drivers or {}).get(pool_key)
        driver = alt if alt else COST_POOLS[pool_key]["primary_driver"]
        print(f"Allocating {pool_key} on driver '{driver}' …")
        cm, recon = allocate_pool(cm, pool_key, driver_col=driver)
        reconciliations.append(recon)
        print(f"  Allocated: R$ {recon['allocated_sum']:,.2f}  | Coverage: {recon['coverage']*100:.1f}%")

    cost_cols = [f"cost_{k}" for k in COST_POOLS]
    cm["cost_to_serve"] = cm[cost_cols].sum(axis=1)
    cm["customer_contribution"] = cm["product_contribution"] - cm["cost_to_serve"]
    cm["breakeven_service_cost"] = cm["product_contribution"]
    cm["service_cost_headroom"] = cm["breakeven_service_cost"] - cm["cost_to_serve"]
    cm["service_cost_intensity"] = np.where(
        cm["net_sales"] > 0,
        cm["cost_to_serve"] / cm["net_sales"],
        np.nan,
    )

    for pool_key, pool in COST_POOLS.items():
        col = f"cost_{pool_key}"
        cm[f"avoidable_{pool_key}"] = cm[col] * pool["avoidable_pct"]
        cm[f"stranded_{pool_key}"] = cm[col] * (1 - pool["avoidable_pct"])

    cm["total_avoidable_cts"] = sum(cm[f"avoidable_{k}"] for k in COST_POOLS)
    cm["total_stranded_cts"] = sum(cm[f"stranded_{k}"] for k in COST_POOLS)

    out_path = PROCESSED / "customer_month_cts.csv"
    cm.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")

    print("\n=== COST-TO-SERVE SUMMARY ===")
    print(f"Total Product Contribution : R$ {cm['product_contribution'].sum():>14,.2f}")
    print(f"Total Cost-to-Serve        : R$ {cm['cost_to_serve'].sum():>14,.2f}")
    print(f"Total Customer Contribution: R$ {cm['customer_contribution'].sum():>14,.2f}")
    print(f"CTS as % of Net Sales      : {cm['cost_to_serve'].sum() / cm['net_sales'].sum() * 100:.1f}%")
    print(f"Positive contribution customers-months : {(cm['customer_contribution'] > 0).sum():,}")
    print(f"Negative contribution customer-months  : {(cm['customer_contribution'] < 0).sum():,}")
    check_cts_share(float(cm['cost_to_serve'].sum()), float(cm['net_sales'].sum()))

    meta = {
        "pools": COST_POOLS,
        "reconciliations": reconciliations,
        "total_cts": float(cm["cost_to_serve"].sum()),
        "total_customer_contribution": float(cm["customer_contribution"].sum()),
    }
    with open(OUTPUTS / "cts_allocation_meta.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    return cm, reconciliations


if __name__ == "__main__":
    run_cost_to_serve()

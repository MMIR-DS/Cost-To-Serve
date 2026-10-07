"""
Financial backbone:
Gross Sales → Net Sales → Product Variable Cost (Modeled) → Product Contribution

Primary grain after aggregation: Customer × Month
"""

from pathlib import Path
import pandas as pd
import numpy as np
import json

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

ASSUMPTIONS = {
    "ASSUMP-001": {
        "category": "Product Cost",
        "description": "Product variable cost as percentage of Net Sales (baseline).",
        "value": 0.35,
        "range": [0.25, 0.45],
        "rationale": "Actual COGS unavailable in public dataset. 35% is a defensible mid-range for multi-category marketplace goods.",
        "source": "Industry heuristic + project design",
        "data_status": "Modeled",
        "sensitivity": "High",
    },
    "ASSUMP-002": {
        "category": "Returns Treatment",
        "description": "Canceled / unavailable orders contribute zero Net Sales and zero Product Contribution.",
        "value": "exclude_from_net",
        "rationale": "Prevents revenue recognition on non-fulfilled orders while still allowing operational cost allocation later.",
        "data_status": "Modeled",
        "sensitivity": "Medium",
    },
}


def load_order_line() -> pd.DataFrame:
    path = PROCESSED / "order_line.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run build_order_line.py first.")
    return pd.read_csv(path)


def compute_net_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Net Sales: canceled/unavailable → 0; freight excluded."""
    df = df.copy()
    df["net_sales"] = np.where(df["is_canceled"], 0.0, df["gross_sales"])
    return df


def compute_product_contribution(
    df: pd.DataFrame, product_cost_pct: float = None
) -> pd.DataFrame:
    if product_cost_pct is None:
        product_cost_pct = ASSUMPTIONS["ASSUMP-001"]["value"]
    df = df.copy()
    df["product_variable_cost"] = df["net_sales"] * product_cost_pct
    df["product_contribution"] = df["net_sales"] - df["product_variable_cost"]
    df["product_cost_pct_used"] = product_cost_pct
    return df


def aggregate_customer_month(df: pd.DataFrame) -> pd.DataFrame:
    """Customer × Month. Logistics drivers on non-canceled lines only."""
    fin = (
        df.groupby(["customer_unique_id", "purchase_year_month"], as_index=False)
        .agg(
            gross_sales=("gross_sales", "sum"),
            net_sales=("net_sales", "sum"),
            product_variable_cost=("product_variable_cost", "sum"),
            product_contribution=("product_contribution", "sum"),
            n_canceled_lines=("is_canceled", "sum"),
            customer_state=("customer_state", "first"),
        )
    )
    active = df[~df["is_canceled"]]
    svc = (
        active.groupby(["customer_unique_id", "purchase_year_month"], as_index=False)
        .agg(
            n_orders=("order_id", "nunique"),
            n_order_lines=("order_item_id", "count"),
            n_products=("product_id", "nunique"),
            total_freight=("freight_value", "sum"),
            total_weight_g=("product_weight_g", "sum"),
            total_volume_cm3=("volume_cm3", "sum"),
            n_delivered_lines=("is_delivered", "sum"),
        )
    )
    agg = fin.merge(svc, on=["customer_unique_id", "purchase_year_month"], how="left")
    for col in [
        "n_orders", "n_order_lines", "n_products",
        "total_freight", "total_weight_g", "total_volume_cm3", "n_delivered_lines",
    ]:
        agg[col] = agg[col].fillna(0)
    return agg.sort_values(["customer_unique_id", "purchase_year_month"])


def run_financial_backbone(product_cost_pct: float = None):
    print("Loading order_line …")
    ol = load_order_line()
    print(f"  {len(ol):,} rows")
    print("Computing Net Sales …")
    ol = compute_net_sales(ol)
    print("Computing Product Contribution …")
    ol = compute_product_contribution(ol, product_cost_pct=product_cost_pct)
    ol_path = PROCESSED / "order_line_finance.csv"
    ol.to_csv(ol_path, index=False)
    print(f"Wrote {ol_path}")
    print("Aggregating to Customer × Month …")
    cm = aggregate_customer_month(ol)
    cm_path = PROCESSED / "customer_month.csv"
    cm.to_csv(cm_path, index=False)
    print(f"Wrote {cm_path} ({len(cm):,} customer-months)")
    print("\n=== FINANCIAL RECONCILIATION (Order-Line Level) ===")
    print(f"Gross Sales          : R$ {ol['gross_sales'].sum():>15,.2f}")
    print(f"Net Sales            : R$ {ol['net_sales'].sum():>15,.2f}")
    print(f"Product Variable Cost: R$ {ol['product_variable_cost'].sum():>15,.2f}")
    print(f"Product Contribution : R$ {ol['product_contribution'].sum():>15,.2f}")
    print(f"Product Cost % used  : {ol['product_cost_pct_used'].iloc[0]*100:.1f}%")
    with open(OUTPUTS / "assumptions_snapshot.json", "w") as f:
        json.dump(ASSUMPTIONS, f, indent=2)
    return ol, cm


if __name__ == "__main__":
    run_financial_backbone()

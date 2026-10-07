"""Order-level economics using shared rates module."""
from pathlib import Path
import pandas as pd
import numpy as np

from src.cost_to_serve.rates import compute_order_table

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"


def build_order_economics():
    ol = pd.read_csv(PROCESSED / "order_line_finance.csv", low_memory=False)
    orders = compute_order_table(ol)
    orders.to_csv(PROCESSED / "order_economics.csv", index=False)
    return orders


def classify_contribution():
    """Classify CM: non_fulfillment_only | economic_negative | positive."""
    cm = pd.read_csv(PROCESSED / "customer_month_cts.csv")
    cm["is_non_fulfillment_only"] = (cm["n_order_lines"] == 0) & (cm["n_canceled_lines"] > 0)
    cm["is_negative"] = cm["customer_contribution"] < 0

    def label(row):
        if row["is_non_fulfillment_only"]:
            return "non_fulfillment_only"
        if row["is_negative"]:
            return "economic_negative"
        return "positive"

    cm["segment"] = cm.apply(label, axis=1)
    summary = cm["segment"].value_counts().to_dict()
    out = {
        "segment_counts": {k: int(v) for k, v in summary.items()},
        "economic_negative_total_brl": float(
            cm.loc[cm["segment"] == "economic_negative", "customer_contribution"].sum()
        ),
        "non_fulfillment_total_brl": float(
            cm.loc[cm["segment"] == "non_fulfillment_only", "customer_contribution"].sum()
        ),
    }
    import json
    with open(OUTPUTS / "cm_segment_summary.json", "w") as f:
        json.dump(out, f, indent=2)
    return out


if __name__ == "__main__":
    o = build_order_economics()
    print(f"Orders: {len(o):,} | V1 neg: {(o['contrib_v1']<0).sum()} | Pass-through neg: {(o['contrib_passthrough']<0).sum()}")
    print(classify_contribution())

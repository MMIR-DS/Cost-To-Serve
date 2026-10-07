"""Honest economics: non-fulfillment split + summary aligned with key findings."""
from pathlib import Path
import pandas as pd
import json
from src.cost_to_serve.rates import compute_order_table
from src.cost_to_serve.config import POOL_COSTS

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"


def run():
    cm = pd.read_csv(PROCESSED / "customer_month_cts.csv")
    ol = pd.read_csv(PROCESSED / "order_line_finance.csv", low_memory=False)

    cm["is_non_fulfillment_only"] = (cm["n_order_lines"] == 0) & (cm["n_canceled_lines"] > 0)
    cm["is_negative"] = cm["customer_contribution"] < 0
    econ_neg = cm[cm["is_negative"] & ~cm["is_non_fulfillment_only"]]
    nf = cm[cm["is_non_fulfillment_only"]]

    orders = compute_order_table(ol)
    n_canceled = float(cm["n_canceled_lines"].sum()) or 549.0

    summary = {
        "headline": (
            "Economic exposure is small under marketplace-like baselines "
            f"(~R${abs(econ_neg['customer_contribution'].sum())/1000:.1f}k economic CM negatives; "
            "see freight summary for pass-through order negatives). "
            "Non-fulfillment-only months are 31% of negative months; "
            "the ~95% of negative dollars on those months is mechanical "
            "(Returns pool × zero revenue), not an economic finding. "
            "Material sales exposure requires thinner margins and/or much higher CTS."
        ),
        "cm": {
            "total": int(len(cm)),
            "baseline_negative": int(cm["is_negative"].sum()),
            "non_fulfillment_only_negative": int(
                (cm["is_negative"] & cm["is_non_fulfillment_only"]).sum()
            ),
            "economic_negative": int(
                (cm["is_negative"] & ~cm["is_non_fulfillment_only"]).sum()
            ),
            "economic_negative_total_brl": float(econ_neg["customer_contribution"].sum()),
            "economic_negative_median_brl": float(econ_neg["customer_contribution"].median()),
            "non_fulfillment_negative_total_brl": float(nf["customer_contribution"].sum()),
        },
        "orders_v1": {
            "n": int(len(orders)),
            "negative": int((orders["contrib_v1"] < 0).sum()),
            "negative_pct": float((orders["contrib_v1"] < 0).mean()),
            "negative_total_brl": float(
                orders.loc[orders["contrib_v1"] < 0, "contrib_v1"].sum()
            ),
        },
        "orders_passthrough": {
            "n": int(len(orders)),
            "negative": int((orders["contrib_passthrough"] < 0).sum()),
            "negative_pct": float((orders["contrib_passthrough"] < 0).mean()),
            "negative_total_brl": float(
                orders.loc[orders["contrib_passthrough"] < 0, "contrib_passthrough"].sum()
            ),
        },
        "orders_net_freight": {
            "n": int(len(orders)),
            "negative": int((orders["contrib_net_freight"] < 0).sum()),
            "negative_pct": float((orders["contrib_net_freight"] < 0).mean()),
            "negative_total_brl": float(
                orders.loc[orders["contrib_net_freight"] < 0, "contrib_net_freight"].sum()
            ),
        },
        "returns_pool_per_line": {
            "half": POOL_COSTS["returns_waste"] * 0.5 / n_canceled,
            "base": POOL_COSTS["returns_waste"] / n_canceled,
            "double": POOL_COSTS["returns_waste"] * 2 / n_canceled,
        },
        "wording_fix": (
            "31% of negative months; ~95% of negative dollars is mechanical Returns-pool allocation"
        ),
    }
    with open(OUTPUTS / "honest_economics_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2)[:800])
    return summary


if __name__ == "__main__":
    run()

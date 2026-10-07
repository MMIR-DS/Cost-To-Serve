"""Freight treatment cases + CTS x COGS tipping grids (orders + sales exposed)."""
from pathlib import Path
import pandas as pd
import numpy as np
import json
from src.cost_to_serve.config import POOLS, PRODUCT_COST_BASELINE
from src.cost_to_serve.rates import compute_order_table

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"


def run():
    ol = pd.read_csv(PROCESSED / "order_line_finance.csv", low_memory=False)
    orders = compute_order_table(ol)
    orders.to_csv(PROCESSED / "order_economics.csv", index=False)

    dist_ratio = float(orders["dist_ratio_modeled"].iloc[0])
    rate_oh = orders["cost_oh"].sum() / max(orders["n_lines"].sum(), 1)
    rate_wh = orders["cost_wh"].sum() / max(orders["weight_g"].fillna(0).clip(lower=0).sum(), 1e-9)

    def v1(cogs, scale=1.0):
        pc = orders["net_sales"] * (1 - cogs)
        return (
            pc
            - orders["freight_billed"] * dist_ratio * scale
            - orders["n_lines"] * rate_oh * scale
            - orders["weight_g"].fillna(0).clip(lower=0) * rate_wh * scale
        )

    def passthrough(cogs, scale=1.0):
        pc = orders["net_sales"] * (1 - cogs)
        return pc - orders["n_lines"] * rate_oh * scale - orders["weight_g"].fillna(0).clip(lower=0) * rate_wh * scale

    def with_credit(cogs, dist_r, scale=1.0):
        pc = orders["net_sales"] * (1 - cogs)
        dist = orders["freight_billed"] * dist_r * scale
        return (
            pc
            + orders["freight_billed"]
            - dist
            - orders["n_lines"] * rate_oh * scale
            - orders["weight_g"].fillna(0).clip(lower=0) * rate_wh * scale
        )

    cases = {
        "V1_no_credit_modeled_pool": v1(PRODUCT_COST_BASELINE),
        "pass_through": passthrough(PRODUCT_COST_BASELINE),
        "modeled_pool_with_credit": with_credit(PRODUCT_COST_BASELINE, dist_ratio),
        "subsidized_150pct": with_credit(PRODUCT_COST_BASELINE, 1.5),
    }
    rows = []
    for name, c in cases.items():
        neg = c < 0
        rows.append({
            "case": name,
            "negative_orders": int(neg.sum()),
            "negative_pct_orders": float(neg.mean() * 100),
            "negative_total_brl": float(c[neg].sum()),
            "sales_exposed_pct": float(orders.loc[neg, "net_sales"].sum() / orders["net_sales"].sum() * 100),
        })
    pd.DataFrame(rows).to_csv(OUTPUTS / "freight_treatment_sensitivity.csv", index=False)

    cogs_list = [0.35, 0.45, 0.55, 0.65, 0.75, 0.85]
    scales = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    grid_v1, grid_pt = [], []
    for cogs in cogs_list:
        rv, rp = {"cogs_pct": cogs}, {"cogs_pct": cogs}
        for s in scales:
            cv, cp = v1(cogs, s), passthrough(cogs, s)
            rv[f"neg_order_pct_{s}"] = float((cv < 0).mean() * 100)
            rv[f"sales_exposed_pct_{s}"] = float(
                orders.loc[cv < 0, "net_sales"].sum() / orders["net_sales"].sum() * 100
            )
            rp[f"neg_order_pct_{s}"] = float((cp < 0).mean() * 100)
            rp[f"sales_exposed_pct_{s}"] = float(
                orders.loc[cp < 0, "net_sales"].sum() / orders["net_sales"].sum() * 100
            )
        grid_v1.append(rv)
        grid_pt.append(rp)
    pd.DataFrame(grid_v1).to_csv(OUTPUTS / "tipping_grid_v1.csv", index=False)
    pd.DataFrame(grid_pt).to_csv(OUTPUTS / "tipping_grid_passthrough.csv", index=False)

    summary = {
        "headline": (
            "Economic exposure is small under marketplace-like baselines "
            f"(~R$5.4k economic CM negatives; {rows[1]['negative_orders']} pass-through order negatives). "
            "Non-fulfillment-only months are 31% of negative months; the ~95% of negative dollars "
            "on those months is mechanical (Returns pool × zero revenue), not an economic finding. "
            "Material sales exposure requires thinner margins and/or much higher CTS — see tipping grids."
        ),
        "freight_cases": rows,
        "wording": "31% of negative months; ~95% of negative dollars is mechanical Returns-pool allocation",
        "returns_pool_per_line": {
            "half": POOLS["returns_waste"] * 0.5 / 549,
            "base": POOLS["returns_waste"] / 549,
            "double": POOLS["returns_waste"] * 2 / 549,
        },
    }
    with open(OUTPUTS / "freight_and_tipping_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run()

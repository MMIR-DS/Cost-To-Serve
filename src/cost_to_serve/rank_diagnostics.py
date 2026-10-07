"""What allocation changes vs a pure revenue ranking (pass-through reference)."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.cost_to_serve.rates import compute_order_table

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"


def _spearman(a, b):
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1]) if len(a) >= 3 else float("nan")


def _top_decile_overlap(score_a, score_b):
    n = len(score_a)
    k = max(1, n // 10)
    top_a = set(np.argsort(-score_a)[:k])
    top_b = set(np.argsort(-score_b)[:k])
    return len(top_a & top_b) / k


def run():
    ol = pd.read_csv(PROCESSED / "order_line_finance.csv", low_memory=False)
    orders = compute_order_table(ol)
    pt = orders["contrib_passthrough"].values
    v1 = orders["contrib_v1"].values
    sales = orders["net_sales"].values

    n = len(orders)
    r_pt = pd.Series(pt).rank(ascending=False).values
    r_sales = pd.Series(sales).rank(ascending=False).values
    big_move = np.abs(r_pt - r_sales) > (0.10 * n)

    pc = orders["product_contribution"].values
    flips = ((pc > 0) & (pt < 0)) | ((pc < 0) & (pt > 0))

    out = {
        "grain": "order",
        "n_orders": int(n),
        "thesis": (
            "At plausible marketplace-like assumptions under pass-through freight, "
            "Modeled service cost is a small perturbation: ranks stay close to revenue, "
            "few signs flip. The tipping grid shows where that stops being true."
        ),
        "what_allocation_changes": {
            "sign_flips_vs_product_contribution_only": int(flips.sum()),
            "sign_flip_pct": float(flips.mean()),
            "top_decile_overlap_vs_net_sales": _top_decile_overlap(pt, sales),
            "rank_moves_more_than_10pct_of_n": int(big_move.sum()),
            "rank_move_pct": float(big_move.mean()),
            "spearman_contrib_vs_net_sales": _spearman(pt, sales),
        },
        "pass_through": {
            "spearman_contrib_vs_net_sales": _spearman(pt, sales),
            "top_decile_overlap_vs_net_sales": _top_decile_overlap(pt, sales),
        },
        "v1_sensitivity": {
            "spearman_contrib_vs_net_sales": _spearman(v1, sales),
            "top_decile_overlap_vs_net_sales": _top_decile_overlap(v1, sales),
        },
        "interpretation": (
            "High Spearman means contribution order is close to a revenue ranking. "
            "Use the tipping grid to see when service cost stops being a small perturbation."
        ),
    }
    with open(OUTPUTS / "rank_diagnostics.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()

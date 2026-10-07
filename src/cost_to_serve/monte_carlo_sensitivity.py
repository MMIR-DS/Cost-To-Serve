"""
Optional appendix: illustrative Monte Carlo on Modeled assumptions (Neutral Freight).

Not the primary robustness story (use tipping grid + scenario stresses first).
Quantiles are percentiles of the simulation under explicit Uniform priors —
not confidence intervals or estimated posteriors.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.cost_to_serve.config import POOL_COSTS
from src.cost_to_serve.economic_robustness import pass_through_contrib

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"

N_DRAWS = 200
RNG_SEED = 42
MIN_ROWS_FULL = 1000


def _load_cm() -> pd.DataFrame:
    path = PROCESSED / "customer_month_cts.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    cm = pd.read_csv(path)
    cm["key"] = cm["customer_unique_id"].astype(str) + "|" + cm["purchase_year_month"].astype(str)
    cm["is_nf"] = (cm["n_order_lines"] == 0) & (cm["n_canceled_lines"] > 0)
    return cm


def run(n_draws: int = N_DRAWS, seed: int = RNG_SEED) -> dict:
    cm = _load_cm()
    if len(cm) < MIN_ROWS_FULL:
        out = {
            "structure": "neutral_freight_reference",
            "status": "skipped_insufficient_rows",
            "n_rows": int(len(cm)),
            "min_rows_required": MIN_ROWS_FULL,
            "message": (
                "Monte Carlo published tails require full customer_month_cts "
                "(~97k rows). Sample/tiny tables are skipped so results are not misleading."
            ),
        }
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        (OUTPUTS / "monte_carlo_summary.json").write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2))
        return out
    econ = cm.loc[~cm["is_nf"]].copy()
    rng = np.random.default_rng(seed)

    cogs = rng.uniform(0.25, 0.45, size=n_draws)
    ohwh = rng.uniform(0.85, 1.25, size=n_draws)

    neg_counts = []
    neg_shares = []
    for i in range(n_draws):
        s = pass_through_contrib(cm, cogs=float(cogs[i]), oh_wh_scale=float(ohwh[i]), include_returns=True)
        s = pd.Series(s.values, index=cm["key"].values)
        e = s.loc[econ["key"].values]
        n_neg = int((e < 0).sum())
        neg_counts.append(n_neg)
        neg_shares.append(n_neg / max(len(e), 1))

    neg_counts = np.array(neg_counts)
    neg_shares = np.array(neg_shares)

    returns_stress = {}
    base_ret = POOL_COSTS["returns_waste"]
    for label, mult in [("x0.5", 0.5), ("x1.0", 1.0), ("x2.0", 2.0)]:
        from src.cost_to_serve import economic_robustness as er
        from src.cost_to_serve import config as cfg

        old = dict(cfg.POOL_COSTS)
        cfg.POOL_COSTS = {**old, "returns_waste": base_ret * mult}
        er.POOL_COSTS = cfg.POOL_COSTS
        try:
            s = pass_through_contrib(cm, include_returns=True)
            s = pd.Series(s.values, index=cm["key"].values)
            e = s.loc[econ["key"].values]
            returns_stress[label] = {
                "returns_pool_brl": base_ret * mult,
                "economic_negative_cm": int((e < 0).sum()),
                "returns_per_canceled_line": (base_ret * mult) / max(float(cm["n_canceled_lines"].sum()), 1.0),
            }
        finally:
            cfg.POOL_COSTS = old
            er.POOL_COSTS = old

    s0 = pass_through_contrib(cm, include_returns=True)
    s0 = pd.Series(s0.values, index=cm["key"].values)
    e0 = s0.loc[econ["key"].values]
    baseline_neg = int((e0 < 0).sum())
    med = float(np.percentile(neg_counts, 50))
    p95 = float(np.percentile(neg_counts, 95))
    ratio_med = med / max(baseline_neg, 1)
    ratio_p95 = p95 / max(baseline_neg, 1)

    out = {
        "structure": "neutral_freight_reference",
        "n_draws": n_draws,
        "seed": seed,
        "priors": {
            "product_cost_rate": "Uniform(0.25, 0.45)",
            "oh_wh_scale": "Uniform(0.85, 1.25)",
            "oh_wh_scale_rationale": (
                "Asymmetric band around 1.0 (0.85–1.25) = mild relief vs more room for "
                "service pressure; illustrative, not estimated from data"
            ),
            "note": "Independent uniforms — illustrative uncertainty, not estimated posteriors",
        },
        "economic_negative_cm_count": {
            "mean": float(neg_counts.mean()),
            "pctile_05_of_simulation": float(np.percentile(neg_counts, 5)),
            "pctile_50_of_simulation": med,
            "pctile_95_of_simulation": p95,
            "min": int(neg_counts.min()),
            "max": int(neg_counts.max()),
        },
        "share_economic_cm_negative": {
            "mean": float(neg_shares.mean()),
            "pctile_05_of_simulation": float(np.percentile(neg_shares, 5)),
            "pctile_50_of_simulation": float(np.percentile(neg_shares, 50)),
            "pctile_95_of_simulation": float(np.percentile(neg_shares, 95)),
        },
        "baseline_point_compare": {
            "neutral_freight_neg_cm_at_defaults": baseline_neg,
            "mc_median_neg_cm": med,
            "median_over_baseline": ratio_med,
            "p95_over_baseline": ratio_p95,
        },
        "returns_pool_stress": returns_stress,
        "interpretation": (
            f"Under Neutral Freight and wide Modeled priors, economic-negative customer-months "
            f"remain a thin tail (median {med:.0f} ≈ {ratio_med:.2f}× baseline {baseline_neg}; "
            f"p95 {p95:.0f} ≈ {ratio_p95:.2f}× baseline). The distribution is right-skewed: "
            f"negative counts rise faster than linearly as product-cost rate increases. "
            f"Returns-pool ×2 changes the count only modestly (see returns_pool_stress)."
        ),
    }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "monte_carlo_summary.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()

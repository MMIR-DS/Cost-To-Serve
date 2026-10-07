"""
Economic robust classes under the NEUTRAL freight reference (pass-through).

Returns pool is allocated on the FULL customer-month table (all canceled lines),
then classes are evaluated on economic months only.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import json

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"
from src.cost_to_serve.config import POOL_COSTS


def _allocate(driver: pd.Series, pool: float) -> pd.Series:
    d = driver.fillna(0).clip(lower=0)
    tot = d.sum()
    if tot <= 0:
        return pd.Series(0.0, index=driver.index)
    return pool * (d / tot)


def pass_through_contrib(
    cm_full: pd.DataFrame,
    cogs: float | None = None,
    oh_wh_scale: float = 1.0,
    oh_driver: str = "n_order_lines",
    wh_driver: str = "total_weight_g",
    include_returns: bool = True,
) -> pd.Series:
    """Pass-through contribution; returns use full-table canceled-line denominator."""
    if cogs is None:
        pc = cm_full["product_contribution"]
    else:
        pc = cm_full["net_sales"] * (1 - cogs)

    oh_pool = POOL_COSTS["order_handling"] * oh_wh_scale
    wh_pool = POOL_COSTS["warehousing"] * oh_wh_scale
    if oh_driver not in cm_full.columns:
        raise KeyError(f"{oh_driver} required")
    oh = _allocate(cm_full[oh_driver], oh_pool)
    wh_col = wh_driver if wh_driver in cm_full.columns else "total_weight_g"
    wh = _allocate(cm_full[wh_col], wh_pool)
    ret = (
        _allocate(cm_full["n_canceled_lines"], POOL_COSTS["returns_waste"])
        if include_returns
        else pd.Series(0.0, index=cm_full.index)
    )
    return pc - oh - wh - ret


def run():
    cm = pd.read_csv(PROCESSED / "customer_month_cts.csv")
    cm["key"] = cm["customer_unique_id"].astype(str) + "|" + cm["purchase_year_month"].astype(str)
    cm["is_nf"] = (cm["n_order_lines"] == 0) & (cm["n_canceled_lines"] > 0)
    cm["is_mixed_cancel"] = (~cm["is_nf"]) & (cm["n_canceled_lines"] > 0)

    if "n_orders" not in cm.columns:
        raise KeyError("n_orders required for OH alternative-driver scenario")

    total_canceled = float(cm["n_canceled_lines"].sum())
    ret_per_line = POOL_COSTS["returns_waste"] / max(total_canceled, 1)
    mixed = cm[cm["is_mixed_cancel"]]
    ret_full = _allocate(cm["n_canceled_lines"], POOL_COSTS["returns_waste"])
    mixed_ret_total = float(ret_full.loc[mixed.index].sum()) if len(mixed) else 0.0
    mixed_canceled_lines = float(mixed["n_canceled_lines"].sum()) if len(mixed) else 0.0
    expected_mixed = ret_per_line * mixed_canceled_lines
    if abs(mixed_ret_total - expected_mixed) > 1.0:
        raise RuntimeError(
            f"Returns mixed allocation mismatch: {mixed_ret_total} vs {expected_mixed}"
        )

    c_with = pass_through_contrib(cm, include_returns=True)
    c_without = pass_through_contrib(cm, include_returns=False)
    ret_implied = (c_without - c_with).astype(float)
    if len(mixed):
        expected_ret = mixed["n_canceled_lines"].values * ret_per_line
        actual_ret = ret_implied.loc[mixed.index].values
        if abs(float((actual_ret - expected_ret).sum())) > 1.0:
            raise RuntimeError(
                "Binding returns check failed: pass_through_contrib mixed-row "
                f"returns {actual_ret.sum():.2f} vs expected {expected_ret.sum():.2f}"
            )

    series_full = {
        "pt_baseline": pass_through_contrib(cm),
        "pt_cogs_25": pass_through_contrib(cm, cogs=0.25),
        "pt_cogs_45": pass_through_contrib(cm, cogs=0.45),
        "pt_ohwh_relief": pass_through_contrib(cm, oh_wh_scale=0.85),
        "pt_ohwh_pressure": pass_through_contrib(cm, oh_wh_scale=1.20),
        "pt_best_corner": pass_through_contrib(cm, cogs=0.25, oh_wh_scale=0.85),
        "pt_worst_corner": pass_through_contrib(cm, cogs=0.45, oh_wh_scale=1.20),
        "pt_oh_on_orders": pass_through_contrib(cm, oh_driver="n_orders"),
        "pt_wh_on_volume": pass_through_contrib(
            cm, wh_driver="total_volume_cm3" if "total_volume_cm3" in cm.columns else "total_weight_g"
        ),
    }

    cm_idx = cm.set_index("key")
    econ_keys = cm.loc[~cm["is_nf"], "key"].values

    series = {}
    for name, s in series_full.items():
        s = pd.Series(s.values, index=cm_idx.index)
        series[name] = s.loc[econ_keys]

    common = series["pt_baseline"].index
    for s in series.values():
        common = common.intersection(s.index)

    all_pos = np.ones(len(common), dtype=bool)
    all_neg = np.ones(len(common), dtype=bool)
    for s in series.values():
        sgn = np.sign(s.loc[common].values)
        all_pos &= sgn > 0
        all_neg &= sgn < 0

    robust_neg_keys = common[all_neg]
    mixed_keys = set(cm.loc[cm["is_mixed_cancel"], "key"])
    robust_neg_mixed = int(sum(1 for k in robust_neg_keys if k in mixed_keys))

    series_nr = {
        k: pd.Series(pass_through_contrib(cm, include_returns=False).values, index=cm_idx.index).loc[econ_keys]
        for k in ["pt_baseline"]
    }
    base_nr = series_nr["pt_baseline"]
    neg_nr = int((base_nr < 0).sum())

    base_pt = series["pt_baseline"]
    v1 = cm_idx.loc[econ_keys, "customer_contribution"]

    out = {
        "universe": "economic_customer_months_only",
        "cost_structure": "pass_through_freight_reference",
        "returns_allocation": "full_cm_denominator_then_subset_economic",
        "returns_per_canceled_line": ret_per_line,
        "total_canceled_lines": total_canceled,
        "mixed_months_with_cancels": int(len(mixed)),
        "mixed_canceled_lines": mixed_canceled_lines,
        "returns_allocated_to_mixed_months_brl": mixed_ret_total,
        "n_economic": int((~cm["is_nf"]).sum()),
        "n_compared": int(len(common)),
        "robust_positive": int(all_pos.sum()),
        "robust_negative": int(all_neg.sum()),
        "sensitive": int((~all_pos & ~all_neg).sum()),
        "robust_negative_mixed_with_cancels": robust_neg_mixed,
        "baseline_negative_pass_through_cm": int((base_pt < 0).sum()),
        "baseline_negative_pass_through_no_returns_cm": neg_nr,
        "baseline_negative_v1_sensitivity": int((v1 < 0).sum()),
        "scenarios_used": list(series.keys()),
        "note": (
            "Returns allocated on full CM (all canceled lines), then economic subset. "
            "robust_negative_mixed_with_cancels counts robust negatives that are mixed months "
            "(active + canceled). Order-level pass-through excludes returns by construction."
        ),
        "baseline_negative_pass_through": int((base_pt < 0).sum()),
    }
    with open(OUTPUTS / "economic_robust_classes.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    run()

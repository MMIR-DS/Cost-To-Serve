"""
Impact × Effort — illustrative tiering of *chosen positive* levers only.

Not an optimization. External pressures and value-down scenarios are listed
separately as risks. Effort scores are analyst-assigned (1=low, 3=high).
"""
from __future__ import annotations

import json
from pathlib import Path

OUTPUTS = Path(__file__).resolve().parents[2] / "outputs"

EFFORT = {
    "price_up_5pct": 2,
    "discount_reduction": 2,
    "lean_delivery": 2,
    "returns_tightening": 2,
    "premium_service": 3,
    "price_down_pressure": 1,
}

SERVICE_STRUCTURE = "modeled_cts_no_freight_credit"
COMMERCIAL_STRUCTURE = "product_bridge_plus_modeled_cts_as_in_scenarios_module"


def _impact_tier(abs_delta: float) -> str:
    if abs_delta >= 400_000:
        return "H"
    if abs_delta >= 150_000:
        return "M"
    return "L"


def _effort_tier(e: int) -> str:
    return {1: "L", 2: "M", 3: "H"}.get(e, "M")


def run() -> dict:
    path = OUTPUTS / "scenarios_summary.json"
    if not path.exists():
        raise FileNotFoundError(path)
    scen = json.loads(path.read_text())

    positive_levers = []
    risk_items = []

    for family in ("commercial", "service_model"):
        for s in scen.get(family, []):
            name = s["scenario"]
            if name == "baseline":
                continue
            delta = float(s.get("delta_customer_contribution", 0.0))
            effort = int(EFFORT.get(name, 2))
            abs_imp = abs(delta)
            row = {
                "family": family,
                "scenario": name,
                "description": s.get("description", ""),
                "delta_customer_contribution_brl": delta,
                "effort_1_low_3_high": effort,
                "impact_tier": _impact_tier(abs_imp),
                "effort_tier": _effort_tier(effort),
                "structure_note": (
                    SERVICE_STRUCTURE if family == "service_model" else COMMERCIAL_STRUCTURE
                ),
            }
            if delta > 0:
                positive_levers.append(row)
            else:
                risk_items.append(row)

    tier_rank = {"H": 0, "M": 1, "L": 2}
    positive_levers.sort(
        key=lambda r: (
            tier_rank[r["impact_tier"]],
            r["effort_1_low_3_high"],
            -r["delta_customer_contribution_brl"],
        )
    )
    risk_items.sort(key=lambda r: r["delta_customer_contribution_brl"])

    out = {
        "title": "Illustrative Impact × Effort (positive levers only)",
        "method": (
            "Tier by |Δ contribution| (H/M/L) and analyst effort (1–3). "
            "Only scenarios with positive Δ appear as levers. "
            "No R$/effort ratio."
        ),
        "positive_levers": positive_levers,
        "risk_or_pressure": risk_items,
        "grid_readme": {
            "impact_tiers": "H ≥ R$400k, M ≥ R$150k, else L (absolute Δ contribution)",
            "effort_tiers": "1=L, 2=M, 3=H (illustrative)",
        },
        "structure_warning": (
            "Service-model deltas inherit the scenarios module (Modeled CTS including "
            "distribution — No Freight Credit layer). Under Neutral Freight Reference, "
            "cutting the distribution pool would not free the same contribution."
        ),
        "guardrail": (
            "Not a recommended investment portfolio. Positive Δ under Modeled assumptions "
            "is not a business case. External pressures are risks, not initiatives."
        ),
    }
    out_path = OUTPUTS / "impact_effort.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2)[:3000])
    return out


if __name__ == "__main__":
    run()

"""
Single source of Modeled pool totals, avoidability, and product-cost baseline.

Pool totals are **fixed Modeled BRL assumptions**, calibrated once against the
baseline Olist extract so total CTS ≈ 10% of Net Sales. They are **not**
dynamically recalculated from Net Sales during allocation.

`POOL_SHARE_OF_CTS` documents the internal mix of the fixed total only.
"""
from __future__ import annotations

PRODUCT_COST_BASELINE = 0.35
PRODUCT_COST_RANGE = (0.25, 0.45)

# Target total CTS as share of Net Sales (Modeled calibration)
CTS_TARGET_SHARE_OF_NET_SALES = 0.10
CTS_SHARE_WARN_LOW = 0.05
CTS_SHARE_WARN_HIGH = 0.20

# Pool shares of *total CTS* (sum to 1.0)
POOL_SHARE_OF_CTS = {
    "order_handling": 250_000 / 1_350_000,   # ≈ 18.5%
    "distribution": 600_000 / 1_350_000,     # ≈ 44.4%
    "warehousing": 400_000 / 1_350_000,      # ≈ 29.6%
    "returns_waste": 100_000 / 1_350_000,    # ≈ 7.4%
}

# Fixed Modeled pool totals (calibrated once; held fixed in the baseline model).
POOL_COSTS = {
    "order_handling": 250_000.0,
    "distribution": 600_000.0,
    "warehousing": 400_000.0,
    "returns_waste": 100_000.0,
}



def check_cts_share(total_cts: float, net_sales: float) -> None:
    """Warn (or raise if extreme) when total CTS is outside the 5–20% band."""
    if net_sales <= 0:
        return
    share = total_cts / net_sales
    if share < CTS_SHARE_WARN_LOW or share > CTS_SHARE_WARN_HIGH:
        msg = (
            f"WARNING: total CTS is {share:.1%} of Net Sales "
            f"(expected roughly {CTS_SHARE_WARN_LOW:.0%}–{CTS_SHARE_WARN_HIGH:.0%}). "
            f"CTS={total_cts:,.0f}, Net Sales={net_sales:,.0f}."
        )
        print(msg)
        if share < 0.02 or share > 0.40:
            raise RuntimeError(msg.replace("WARNING: ", "CTS share out of bounds: "))


COST_POOLS = {
    "order_handling": {
        "name": "Order Handling",
        "activity": "Order entry, processing, validation, administration",
        "primary_driver": "n_order_lines",
        "driver_description": "Number of order lines (each line requires processing)",
        "pool_cost": POOL_COSTS["order_handling"],
        "avoidable_pct": 0.70,
        "rationale_size": "Share of Modeled CTS; calibrated so total CTS ≈ 10% of Net Sales.",
        "alternative_drivers": ["n_orders"],
    },
    "distribution": {
        "name": "Distribution",
        "activity": "Shipment, loading, transportation, last-mile delivery",
        "primary_driver": "total_freight",
        "driver_description": "Observed freight value charged (proxy for logistics effort — not internal cost)",
        "pool_cost": POOL_COSTS["distribution"],
        "avoidable_pct": 0.80,
        "rationale_size": "Largest pool share. Billed freight is a proxy, not platform logistics cost.",
        "alternative_drivers": ["total_weight_g", "n_orders"],
    },
    "warehousing": {
        "name": "Warehousing",
        "activity": "Picking, packing, handling, storage, movement",
        "primary_driver": "total_weight_g",
        "driver_description": "Total product weight handled (proxy)",
        "pool_cost": POOL_COSTS["warehousing"],
        "avoidable_pct": 0.40,
        "rationale_size": "Physical-weight proxy; marketplace sellers often fulfill.",
        "alternative_drivers": ["total_volume_cm3", "n_order_lines"],
    },
    "returns_waste": {
        "name": "Returns / Non-Fulfillment",
        "activity": "Non-fulfillment handling (canceled/unavailable proxy — not true physical returns)",
        "primary_driver": "n_canceled_lines",
        "driver_description": "Canceled / unavailable lines as non-fulfillment proxy",
        "pool_cost": POOL_COSTS["returns_waste"],
        "avoidable_pct": 0.90,
        "rationale_size": "Small share; allocation to zero-revenue months is mechanical.",
        "alternative_drivers": ["n_orders"],
    },
}

POOLS = POOL_COSTS

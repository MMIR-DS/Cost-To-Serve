"""Shared Modeled cost rates — single source for order-level calculations."""
from __future__ import annotations
import pandas as pd
from src.cost_to_serve.config import POOLS


def compute_order_table(order_line: pd.DataFrame) -> pd.DataFrame:
    """Active (non-canceled) order-level economics with shared rates."""
    active = order_line[~order_line["is_canceled"]].copy()
    orders = (
        active.groupby("order_id", as_index=False)
        .agg(
            customer_unique_id=("customer_unique_id", "first"),
            purchase_year_month=("purchase_year_month", "first"),
            n_lines=("order_item_id", "count"),
            net_sales=("net_sales", "sum"),
            product_contribution=("product_contribution", "sum"),
            freight_billed=("freight_value", "sum"),
            weight_g=("product_weight_g", "sum"),
            customer_state=("customer_state", "first"),
        )
    )
    rate_oh = POOLS["order_handling"] / max(orders["n_lines"].sum(), 1)
    rate_dist = POOLS["distribution"] / max(orders["freight_billed"].sum(), 1e-9)
    rate_wh = POOLS["warehousing"] / max(orders["weight_g"].fillna(0).clip(lower=0).sum(), 1e-9)
    orders["cost_oh"] = orders["n_lines"] * rate_oh
    orders["cost_dist"] = orders["freight_billed"] * rate_dist
    orders["cost_wh"] = orders["weight_g"].fillna(0).clip(lower=0) * rate_wh
    orders["cts_v1"] = orders["cost_oh"] + orders["cost_dist"] + orders["cost_wh"]
    orders["contrib_v1"] = orders["product_contribution"] - orders["cts_v1"]
    orders["contrib_passthrough"] = (
        orders["product_contribution"] - orders["cost_oh"] - orders["cost_wh"]
    )
    orders["contrib_net_freight"] = (
        orders["product_contribution"]
        + orders["freight_billed"]
        - orders["cost_dist"]
        - orders["cost_oh"]
        - orders["cost_wh"]
    )
    orders["dist_ratio_modeled"] = rate_dist
    return orders

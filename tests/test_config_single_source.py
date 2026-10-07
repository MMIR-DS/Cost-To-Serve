"""Pool totals must come from config everywhere allocation is defined."""
from src.cost_to_serve.config import POOL_COSTS, COST_POOLS, PRODUCT_COST_BASELINE
from src.cost_to_serve.pools_and_allocation import COST_POOLS as ALLOC_POOLS


def test_alloc_pools_match_config():
    for k, v in POOL_COSTS.items():
        assert ALLOC_POOLS[k]["pool_cost"] == v
        assert COST_POOLS[k]["pool_cost"] == v


def test_product_cost_baseline_in_range():
    assert 0.20 <= PRODUCT_COST_BASELINE <= 0.50

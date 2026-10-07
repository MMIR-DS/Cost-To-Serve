# Data dictionary — Customer Contribution After Cost-to-Serve

Lightweight **business-facing** dictionary. Intermediate pandas columns stay in code/docstrings.

---

## Analytical conventions (semantic contract)

| Tag | Meaning |
|-----|--------|
| **Observed** | Directly available in Olist |
| **Derived** | Calculated from observed data without a new economic assumption |
| **Modeled** | Requires an assumption about cost, allocation, or economics |
| **Scenario** | Deliberately changes a Modeled assumption to test sensitivity |

**Hard rules**

- **Negative ≠ unprofitable.** Means negative *Modeled contribution* under the stated structure/scenario.
- **Customer-month ≠ customer lifetime profitability.**
- **Product Variable Cost ≠ observed accounting COGS.**
- **Cost-to-Serve ≠ actual ERP/accounting service cost.**
- **Robust ≠ universally robust.** Means stable across the *explicitly tested* scenario set.
- **Neutral Freight Reference** is an analytical treatment, not a claim of contractual freight pass-through accounting.

---

## Grain ladder

```text
order_line          →  physical / product / freight attributes
        ↓
order               →  fulfillment & order-level contribution
        ↓
customer × month    →  recurring comparison, allocation, robustness classes
```

| Grain | Table / artifact | Allowed questions |
|-------|------------------|-------------------|
| **Order line** | `order_line` / `order_line_finance` | Item value, freight, weight, cancel flag, line product economics |
| **Order** | `order_economics` | Order contribution under Neutral Freight Reference vs Modeled CTS — No Freight Credit |
| **Customer × month** | `customer_month_cts` | Monthly contribution after service cost; robust / sensitive classes |

---

## Core fields

| Field / display name | Meaning | Grain | Type |
|----------------------|---------|-------|------|
| `order_id` | Unique Olist order | Order | Observed |
| `order_item_id` | Line within order | Order line | Observed |
| `customer_unique_id` | Customer identifier | Customer | Observed |
| `purchase_year_month` | Month assigned for aggregation | Order / CM | Derived |
| `price` / item value | Product value (freight separate) | Order line | Observed |
| `freight_value` | Freight charged to customer | Order line | Observed |
| `product_weight_g` | Product weight | Order line | Observed |
| `is_canceled` | Non-fulfilled / canceled treatment | Order line | Derived |
| `net_sales` | Sales after defined exclusions (e.g. cancels) | Line → roll up | Derived |
| `product_variable_cost` | Modeled product cost (baseline ~35% of net sales) | Line → roll up | **Modeled** |
| `product_contribution` | Net sales − product variable cost | Line → roll up | Derived from Modeled |
| `cost_order_handling` | Allocated order-handling CTS | CM (from lines) | **Modeled** |
| `cost_distribution` | Allocated distribution CTS | CM | **Modeled** |
| `cost_warehousing` | Allocated warehousing CTS | CM | **Modeled** |
| `cost_returns_waste` | Non-Fulfillment / Returns **Proxy** pool allocation | CM | **Modeled** |
| `cost_to_serve` | Sum of allocated CTS pools | CM | **Modeled** |
| `customer_contribution` | Customer Contribution After Cost-to-Serve | CM | Derived from Modeled |
| `service_cost_intensity` | CTS ÷ net sales | CM | Derived |
| `service_cost_headroom` | Product contribution − CTS | CM | Derived |
| `contrib_passthrough` | Order contribution under Neutral Freight Reference | Order | Derived from Modeled |

---

See also: [definitions.md](definitions.md), [cost_driver_mapping.md](cost_driver_mapping.md).

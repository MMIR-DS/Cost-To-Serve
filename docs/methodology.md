# Methodology — Customer Contribution After Cost-to-Serve

## Analytical Grain

| Level | Grain | Use |
|-------|-------|-----|
| Base | Order Line | Cleaning, driver construction, validation |
| Primary reporting | Customer × Month | Contribution, robustness, allocation |
| **Decision grain (this dataset)** | **Order** | Preferred for interpretation (repeat rate ~3%); see order-level & freight page |
| Diagnostic | Product / State / Category | Drill-down only |

No artificial channel was invented.

---

## Financial Bridge

```
Gross Sales
  − Canceled / Unavailable lines
= Net Sales
  − Product Variable Cost (Modeled %)
= Product Contribution
  − Cost-to-Serve (4 Modeled pools)
= Customer Contribution
```

- Freight is excluded from Net Sales (treated as service-cost proxy).
- Product Variable Cost % is Modeled (baseline 35%, tested 25–45%).

---

## Cost-to-Serve Framework

Four pools only (V1):

1. **Order Handling** — driver: order lines  
2. **Distribution** — driver: observed freight value  
3. **Warehousing** — driver: product weight  
4. **Returns / Non-Fulfillment (proxy)** — driver: canceled lines  

Allocation rule (all pools):

```
Allocated Cost = Pool Cost × (Customer Driver / Total Driver)
```

100% coverage under primary drivers. Alternative drivers tested in Robustness.

---

## Avoidable vs Stranded

Pool-level modeling assumptions only.  
They exist to prevent the false inference that “negative contribution → fire customer → 100% of allocated cost disappears.”

---

## Robustness Design

| Axis | Levels Tested |
|------|---------------|
| Product cost % | 25%, 35%, 45% |
| Pool sizes | −15%, baseline, +20% |
| Drivers | Primary vs Alternative set |
| Operating regimes | Standard, Freight-Heavy, Handling-Heavy, High-Return |

Outputs: Contribution range, Break-even range, Sign stability, Rank stability.

---

## Decision Scenarios

Only two families:

- **Commercial Terms**: price, effective discount  
- **Service Model**: delivery intensity, handling, returns policy  

Cost-driver assumptions remain inside Robustness, keeping the model conceptually clean.

---

## Validation

Automated pytest suite covers financial identities, pool reconciliation, driver totals, allocation coverage, scenario baseline deltas = 0, and sign/rank stability thresholds.

---

## Data Classification Hierarchy

| Tier | Meaning | Examples |
|------|---------|----------|
| 1 Observed | Directly from Olist | price, freight, weight, status |
| 2 Derived | Calculated from observed | net_sales, n_lines, delivery days |
| 3 Modeled | Requires cost assumption | pool sizes, product cost %, avoidability |
| 4 Scenario | Stresses a Modeled input | price +5%, lean delivery |

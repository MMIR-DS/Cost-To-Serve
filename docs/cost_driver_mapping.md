# Cost Driver Mapping — Customer Contribution After Cost-to-Serve

Principle: *Do not allocate cost simply because revenue exists. Identify the operational activity that creates the cost and use a defensible driver to allocate it.*

---

## Pool 1 — Order Handling

| Element | Detail |
|---------|--------|
| **Activity** | Order entry, processing, validation, administration |
| **Candidate Drivers** | Number of orders, Number of order lines, Units handled |
| **Selected Primary Driver** | `n_order_lines` |
| **Allocation Rule** | Pool Cost × (Customer order lines / Total order lines) |
| **Causal Relevance** | Each additional line requires processing work |
| **Data Availability** | Observed / Derived from order_item rows |
| **Granularity** | Customer × Month |
| **Interpretability** | High — operations managers understand line complexity |

---

## Pool 2 — Distribution

| Element | Detail |
|---------|--------|
| **Activity** | Shipment, loading, transportation, delivery |
| **Candidate Drivers** | Freight value, Delivery count (orders), Weight, Volume / Distance |
| **Selected Primary Driver** | `total_freight` (observed) |
| **Allocation Rule** | Pool Cost × (Customer freight / Total freight) |
| **Causal Relevance** | Freight charged is the best available proxy for logistics effort in this dataset |
| **Data Availability** | Observed on every order line |
| **Alternative Drivers** | `total_weight_g`, `n_orders` (tested in Robustness) |
| **Interpretability** | High |

---

## Pool 3 — Warehousing

| Element | Detail |
|---------|--------|
| **Activity** | Picking, packing, handling, storage, movement |
| **Candidate Drivers** | Units, Weight, Volume (L×H×W), Warehouse movements |
| **Selected Primary Driver** | `total_weight_g` |
| **Allocation Rule** | Pool Cost × (Customer weight / Total weight) |
| **Causal Relevance** | Heavier products require more handling effort and space |
| **Data Availability** | Observed (product_weight_g) almost complete |
| **Alternative Drivers** | `total_volume_cm3`, `n_order_lines` |
| **Interpretability** | High |

---

## Pool 4 — Returns / Non-Fulfillment (proxy)

| Element | Detail |
|---------|--------|
| **Activity** | Return processing, inspection, handling, waste |
| **Candidate Drivers** | Returned units, Return transactions, Canceled lines |
| **Selected Primary Driver** | `n_canceled_lines` |
| **Allocation Rule** | Pool Cost × (Customer canceled lines / Total canceled lines) |
| **Causal Relevance** | Canceled / unavailable status is the observable proxy for non-fulfillment activity that generates handling cost |
| **Data Availability** | Derived from order_status |
| **Caveat** | Low absolute volume in Olist; pool sized modestly |
| **Interpretability** | Acceptable — clearly documented as proxy |

---

## Allocation Coverage

By construction the primary allocation uses 100% of each pool (no unallocated residual under the primary drivers).  
If an alternative driver has zero total, coverage falls and is reported.

---

## Short-Run vs Long-Run

Avoidability percentages (ASSUMP-007) are applied at pool level only.  
They communicate that a negative Customer Contribution does **not** imply that 100% of the allocated cost would disappear if the customer were lost.

# Canonical vocabulary — Customer Contribution After Cost-to-Serve

Use these terms **exactly** in docs, dashboard, and interviews.  
Field-level detail: [`data_dictionary.md`](data_dictionary.md).

---

## Semantic contract (short)

| Tag | Meaning |
|-----|--------|
| **Observed** | In Olist directly |
| **Derived** | From observed data, no new cost assumption |
| **Modeled** | Requires cost/allocation assumption |
| **Scenario** | Stresses a Modeled assumption |

Negative ≠ accounting loss. Customer-month ≠ lifetime P&L. Robust = stable on the **tested** set only.

---

## Contribution structures

| Business label | Internal | Definition |
|----------------|----------|------------|
| **Neutral Freight Reference** | `pass_through` | Freight assumed to offset distribution one-for-one; order contrib ≈ PC − OH − WH |
| **Modeled CTS — No Freight Credit** | `v1` | Full Modeled CTS including distribution; no freight credit |
| **Freight Subsidy Stress** | subsidized | Distribution cost stressed above billed freight |

Prefer business labels on the dashboard; internal code names may remain `pass_through` / `v1`.

---

## Negatives (always state grain + structure)

| Term | Definition | Approx. value |
|------|------------|---------------:|
| Pure non-fulfillment negative CM | Only canceled lines; mechanical Non-Fulfillment / Returns Proxy | 458 |
| **Economic Negative Customer-Month** (No Freight Credit) | Negative CM after excluding pure NF under Modeled CTS — No Freight Credit | 1,005 |
| **Economic Negative Customer-Month** (Neutral Freight) | Negative CM under Neutral Freight Reference | **104** (96 without returns) |
| **Negative Order Contribution** (Neutral Freight) | Order-level PC − OH − WH < 0 | **101** |
| Robust negative CM | Negative under all tested Neutral Freight stresses | **21** (7 mixed with cancels) |

---

## Headline bridge metric

**Customer Contribution After Cost-to-Serve**  
`= Net Sales − Product Variable Cost − Cost-to-Serve`  
(at customer-month or order grain as stated)

**Product Variable Cost** — keep this name (not “COGS”); cost rate is Modeled.

---

## Cost pools

1. Order Handling  
2. Distribution  
3. Warehousing  
4. **Non-Fulfillment / Returns Proxy**

---

## Headline numbers (Neutral Freight Reference unless noted)

| Label | Value |
|-------|------:|
| Negative Order Contribution | 101 |
| Economic Negative Customer-Months | 104 |
| Same, returns excluded | 96 |
| Robust negative CM | 21 (7 mixed) |
| Robust positive / sensitive | 96,438 / 402 |
| Returns proxy R$ / canceled line | ~182 (Modeled average) |

Source: `outputs/economic_robust_classes.json`, `freight_and_tipping_summary.json`.

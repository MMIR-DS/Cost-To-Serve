# Assumption Register — Customer Contribution After Cost-to-Serve

All Modeled assumptions are explicit. None are observed accounting costs.

---

## Product economics

| ID | Assumption | Baseline | Range tested | Sensitivity |
|----|------------|----------|--------------|-------------|
| ASSUMP-001 | Product variable cost % of Net Sales | 35% | 25–45% (grid); Uniform draws in Monte Carlo | High |
| ASSUMP-002 | Canceled / unavailable → zero Net Sales | Exclude from net | Fixed | Medium |

---

## Cost-to-Serve pools (from `config.py`)

| Pool | Pool cost (BRL) | Primary driver | Avoidable % |
|------|----------------:|----------------|-------------|
| Order Handling | 250,000 | `n_order_lines` | 70% |
| Distribution | 600,000 | `total_freight` (proxy) | 80% |
| Warehousing | 400,000 | `total_weight_g` | 40% |
| Returns / Non-Fulfillment | 100,000 | `n_canceled_lines` | 90% |
| **Total** | **1,350,000** | | |

Calibration: total CTS ≈ 10% of Net Sales (~R$13.5M). This is a **Modeled baseline**, not an industry-validated rate. See `docs/industry_context.md`.

---

## Freight treatments

| Case | Treatment | Role |
|------|-----------|------|
| **Neutral Freight Reference** | Distribution cost = billed freight → nets to zero | **Headline reference** |
| Modeled CTS — No Freight Credit | Full distribution pool, no credit | Sensitivity |
| Modeled 27% with credit | Credit at modeled cost share | Sensitivity |
| Subsidized 150% | Charge 1.5× billed freight | Stress |

---

## Returns rate

~R$182 per canceled line = pool size ÷ total canceled lines (Modeled average). Does not vary by order value. Sensitivity: pool ×0.5 / ×1 / ×2 → economic-negative CM **100 / 104 / 105**.

---

## What is *not* assumed

- True Olist COGS or warehouse ownership
- Platform take-rate / commission P&L
- That dropping a negative customer recovers 100% of allocated cost (use Avoidable vs Stranded)

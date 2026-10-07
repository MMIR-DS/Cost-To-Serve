# See also: [Canonical vocabulary](definitions.md)

# Key Findings — Customer Contribution After Cost-to-Serve

## Thesis

**At plausible marketplace-like assumptions under a transparent Neutral Freight Reference, Modeled service cost is a small perturbation** — ranks stay close to revenue (Spearman ≈ 0.99), few signs flip, and only a thin tail is robustly negative. **The tipping grid shows where that stops being true** (thin margins and/or much higher CTS).

This is **not** a claim that Cost-to-Serve “reveals hidden unprofitable customers” on Olist under baseline assumptions.

---

## Reference cost structure: Neutral Freight Reference

Distribution cost = billed freight → nets to zero. Live service cost ≈ **order handling + warehousing** (≈ **4.8%** of net sales at baseline pools), plus Returns on canceled lines in mixed months.

| Metric | Value |
|--------|------:|
| **Neutral Freight Reference negative orders** | **101** (−R$779) |
| % of sales exposed | **0.027%** |
| **Neutral Freight Reference negative customer-months** | **104** (**96** without returns) |
| Robustly negative customer-months (tested scenarios) | **21** (**7** mixed with cancels) |
| Robust positive | **96,438** |
| Sensitive | **402** |

Driver stress included: OH on `n_orders`, WH on volume when available; COGS / OH+WH scale corners.

---

## Modeled CTS — No Freight Credit (sensitivity) (not the headline)

**Modeled CTS — No Freight Credit** charges the distribution pool with **no** freight credit (total CTS ≈ 10% of sales).

| Segment | Count | Total $ |
|---------|------:|--------:|
| Baseline negative CM (all) | 1,463 | −R$ 103.4k |
| Non-fulfillment only | 458 (**31%** of neg. months) | −R$ 98.0k (**~95%** of neg. $) — **mechanical** |
| Economic (had active lines) | 1,005 | **−R$ 5.4k** |
| Neg. orders | 1,029 | −R$ 4.5k (**0.17%** of sales) |

### Returns-pool sensitivity (per canceled line)

| Pool | ≈ R$ / canceled line |
|------|---------------------:|
| Half | ~91 |
| Base | ~182 |
| Double | ~364 |

---

## What allocation changes (order grain, pass-through)

See `outputs/rank_diagnostics.json`:

| Diagnostic | Approx. |
|------------|--------:|
| Spearman(contrib, net sales) | 0.99 |
| Top-decile overlap vs sales | 0.97 |
| Sign flips vs product contribution only | **101** (0.10%) |
| Rank moves > 10% of N | **2.2%** of orders |

---

## Freight cases (order level)

| Case | Neg. orders | % sales exposed |
|------|------------:|----------------:|
| Modeled CTS — No Freight Credit (sensitivity) | 1,029 | 0.17% |
| **Neutral Freight Reference (reference)** | **101** | **0.027%** |
| Subsidized 150% billed | 3,690 | 0.66% |

---

## Tipping grids

- **Reference:** `tipping_grid_passthrough.csv` (CTS intensity ≈ 4.8% at ×1.0)
- **Sensitivity:** `tipping_grid_v1.csv` (≈ 9.3% order-level CTS at ×1.0)

Materiality = **sales exposed**.

At baseline (35% COGS, ×1.0 Neutral Freight CTS), sales exposed ≈ **0.027%**. At the same COGS with roughly **3×** OH+WH intensity, sales exposed rises to about **1.5%**.

COGS rows **above 45%** on the grid are **stress exploration** beyond the core 25–45% Modeled range.

---

## Does not claim

- True Olist COGS, warehouse ownership, or **platform take-rate P&L**
- That baseline CTS “finds” a large unprofitable customer set
- Termination policy

```bash
python run_pipeline.py
```

**Returns rate:** ~R$182 per canceled line is **pool size ÷ total canceled lines** (Modeled average).

---

## Supporting appendices (not the headline story)

### Calibration posture
See `docs/industry_context.md`. **Do not** present 10% CTS as “industry validated.”

### Optional: illustrative Monte Carlo
`outputs/monte_carlo_summary.json` — supplementary uncertainty illustration under Uniform priors.
Primary robustness: **scenario grid → corners → drivers → robust classification → tipping grid**.

Returns pool ×0.5 / ×1 / ×2 → economic-negative CM **100 / 104 / 105**.

### Illustrative Impact × Effort
`outputs/impact_effort.json` — ranks **positive-Δ** levers by impact/effort *tiers*.
Service-model deltas use **Modeled CTS — No Freight Credit** structure (not Neutral Freight).

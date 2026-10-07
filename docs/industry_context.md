# Industry context (calibration posture)

**Purpose:** Explain how baseline pool intensity was chosen without treating external benchmarks as validation.  
**Not:** proof that Olist’s true service cost is 10% of sales.

---

## Project anchors

| Item | Baseline | Role |
|------|----------|------|
| Total Modeled CTS / net sales | ~**10%** (R$1.35M / R$13.49M) | Modeled CTS — No Freight Credit layer |
| OH+WH only / net sales | ~**4.8%** at ×1.0 | Neutral Freight Reference (live service cost) |
| Product Variable Cost rate | **35%** (stress 25–45%) | Modeled parameter |

Pools are **fixed BRL totals**, calibrated once so total CTS is about 10% of baseline Net Sales, then held fixed. They are not re-derived each run from a formula tied to external “industry truth.”

---

## Why we do **not** lean on a published % band

Public fulfillment / logistics figures vary by channel, geography, service level, and whether the boundary is pick-pack-ship only or broader opex. A single **5–15% of sales** (or any other) band is **not** used here as validation of the pools.

This project’s defense of the baseline is:

1. **Transparency** — pools and product-cost rate are Modeled and named as such.  
2. **Sensitivity** — tipping grid, corners, driver alternatives, robust classes.  
3. **Optional appendix** — illustrative Monte Carlo under explicit uniform priors (not posteriors).

> **10% is a calibrated modeling baseline, not an industry-validated cost.**  
> The decision-relevant question is how contribution conclusions move when service-cost intensity moves away from that baseline.

---

## Related artifacts

| Artifact | Role |
|----------|------|
| Tipping grid | When Modeled CTS stops being a small perturbation |
| `monte_carlo_summary.json` | Optional uncertainty illustration (full CTS required) |
| `impact_effort.json` | Illustrative prioritization of positive levers only |

See `assumptions.md`, `key_findings.md`, `limitations.md`.

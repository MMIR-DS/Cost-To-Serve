# Limitations & Production-Readiness Boundary

## Explicit Non-Goals (V1)

- Full accounting profitability / GAAP / IFRS P&L  
- Company-specific ERP cost rates or actual warehouse labor minutes  
- Customer lifetime value, acquisition cost, or marketing attribution  
- Real-time operational decisioning or automated order blocking  
- Quantity = 1 per order-item row (Olist schema design).  
- Currency is BRL; no FX conversion is applied.

## Modeling Limitations

- Pool sizes are calibrated transparently (~10% of Net Sales) for analytical clarity, not derived from a company’s cost ledger.  
- Avoidability percentages are pool-level assumptions, not customer-specific observed facts.  
- Distance is available via geo but not used as primary Distribution driver in baseline Modeled CTS (freight value is stronger and fully observed).  

## Interpretation Guardrails

1. A negative Customer Contribution after allocated cost does **not** mean the company loses that amount of cash if the customer is dropped.  
2. Rankings and signs are robust under the tested ranges; exact BRL figures are assumption-dependent.  
3. Management response should consider commercial and service levers before any termination decision.  

## Production-Readiness Boundary

This project is a **portfolio-grade analytical prototype**.

A production Cost-to-Serve system would additionally require:

- ERP + WMS + TMS + Returns-system integration  
- Actual finance cost pools and rates  
- Customer-master and contract/service-level governance  
- Data-quality monitoring and automated refresh  
- Security, access control, audit trails  

None of the above are claimed or implemented in V1.

## Engineering notes

- Pool sizes: `src/cost_to_serve/config.py` only.
- Commercial/service scenarios are illustrative arithmetic; prefer tipping grid for claims.
- Raw Olist reconciliation tests run only when `data/raw/olist/` is present.
- Full-CM sign stability ≥99% is dominated by the positive mass; use economic-only robust classes.

## Platform take-rate vs merchant CTS layer

Olist is a marketplace-style platform (sellers often fulfill). This project does **not** model Olist’s commission / take-rate P&L. The 35% product-cost rate and warehousing pool are a **Modeled merchant-style Cost-to-Serve layer** on public order data, used to test sensitivity of contribution conclusions — not to restate Olist’s actual economics. Prefer the Neutral Freight Reference and the tipping grid over any single ranking of “bad customers.”

**Returns rate:** ~R$182 per canceled line is **pool size ÷ total canceled lines** (Modeled average), not an observed returns-processing invoice. It does not vary by order value; returns-pool ×0.5/×1/×2 yields economic-negative CM **100 / 104 / 105** (see key_findings and monte_carlo_summary.json).

[![CI](https://github.com/MMIR-DS/Cost-To-Serve/actions/workflows/ci.yml/badge.svg)](https://github.com/MMIR-DS/Cost-To-Serve/actions/workflows/ci.yml)

# Customer Contribution After Cost-to-Serve

**Portfolio-grade analytical prototype** · Commercial Finance × Supply Chain × Business Analytics

> Under transparent Modeled assumptions, service cost may be only a **small perturbation**.  
> The work is to separate observed from Modeled economics, test alternative assumptions, and show **where the answer breaks**.

---

## 60-second story

1. **Observed** Olist transactions (orders, lines, freight, weight, cancels).  
2. **Financial bridge:** Net Sales → Product Variable Cost (Modeled) → Product Contribution → Cost-to-Serve → **Customer Contribution After Cost-to-Serve**.  
3. **Headline structure:** **Neutral Freight Reference** (billed freight offsets distribution).  
4. **Sensitivity:** Modeled CTS — No Freight Credit; mechanical vs economic negatives.  
5. **Robustness:** selected stresses → robustly negative customer-months → **tipping grid**.  
6. **Not claimed:** accounting profit, ERP Cost-to-Serve, or industry-validated 10% CTS.

**Thesis (Neutral Freight Reference):** ~**101** negative order contributions · ~**104** economic-negative customer-months · ~**0.027%** of sales exposed · **21** robustly negative CM (**7** mixed with cancels). At ~**3×** OH+WH intensity, exposure rises to ~**1.5%** of sales.

Details: [`docs/key_findings.md`](docs/key_findings.md) · vocabulary: [`docs/definitions.md`](docs/definitions.md) · fields: [`docs/data_dictionary.md`](docs/data_dictionary.md)

## Financial bridge (Olist baseline)

| Step | ≈ R$ |
|------|------:|
| Net sales | 13.49M |
| Product contribution (35% Product Variable Cost) | 8.77M |
| Cost-to-Serve (four Modeled pools) | 1.35M |
| **Customer Contribution After Cost-to-Serve** | 7.42M |

## Run

```bash
pip install -e .
python run_pipeline.py --tests
streamlit run app/streamlit_app.py
```

| Command | Purpose |
|---------|--------|
| `python run_pipeline.py` | Ingest → clean → finance → CTS → robustness → scenarios → insights |
| `pytest` | Fixtures + sample always; full-data tests when raw/processed present |
| `streamlit run app/streamlit_app.py` | Dashboard (FULL or SAMPLE mode) |

**Primary robustness:** deterministic stresses → classification → tipping grid.  
**Appendix only:** illustrative Monte Carlo (not confidence intervals).  
**Calibration:** fixed pool totals ≈ 10% of baseline net sales — **not** industry validation.

## Production boundary

Portfolio prototype on **public** data + **Modeled** cost layer.  
Not a production enterprise Cost-to-Serve system. Negative contribution ≠ exit recommendation.

Limitations: [`docs/limitations.md`](docs/limitations.md)

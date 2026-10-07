# Sample data

Small extracts (~100 rows) for **code-only** pytest and dashboard demos when full `data/processed/` is absent.

| File | Purpose |
|------|--------|
| `customer_month_sample.csv` | Pre-CTS customer × month |
| `customer_month_cts_sample.csv` | After allocation |
| `order_line_finance_sample.csv` | Order-line finance grain |

**Full pipeline:** run `python run_pipeline.py` (downloads Olist if needed) to regenerate complete tables under `data/processed/`.

If a sample CSV is incomplete on GitHub, restore from the portfolio zip release asset.

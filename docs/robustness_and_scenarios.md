# Robustness & Decision Scenarios

**Thesis:** under Neutral Freight Reference, Modeled service cost is a small perturbation; the tipping grid maps where it stops.

Returns on full CM canceled lines (~R$182/line). See `outputs/rank_diagnostics.json` for rank vs revenue.

| Class | Count |
|------:|------:|
| Robust positive | 96,438 |
| Robust negative | **21** (7 mixed with cancels) |
| Sensitive | 402 |

Neutral Freight neg. **customer-months**: **104** (96 without returns).  
Neutral Freight neg. **orders**: **101**.

```bash
python run_pipeline.py
```

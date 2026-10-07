# Dataset Gate Report — Customer Contribution After Cost-to-Serve

**Date:** 2026-10-02  
**Dataset Evaluated:** Brazilian E-Commerce Public Dataset by Olist  
**Source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
**Decision:** **ACCEPT**

---

## 1. Executive Gate Outcome

The Olist dataset **passes the Dataset Gate** and is frozen as the transactional backbone for Customer Contribution After Cost-to-Serve.

It provides a clean order-line structure, strong commercial fields, and — critically for Cost-to-Serve — multiple defensible operational proxies (freight value, product weight/dimensions, delivery timestamps, geolocation, order complexity, and cancellation signals).

A calibrated synthetic layer is required for the four cost pools (Order Handling, Distribution, Warehousing, Returns & Waste), but the observed drivers are of high quality.

---

## 2. Dataset Snapshot

| Table | Rows | Key Purpose |
|-------|-----:|-------------|
| olist_orders_dataset | 99,441 | Order header, status, timestamps |
| olist_order_items_dataset | 112,650 | Order lines, price, freight, seller |
| olist_customers_dataset | 99,441 | Customer unique ID, geo |
| olist_products_dataset | 32,951 | Category, weight, dimensions |
| olist_sellers_dataset | 3,095 | Seller location |
| product_category_name_translation | 71 | Category English names |

**Time span:** 2016-09-04 → 2018-10-17 (~2 years)

---

## 3. Customer Structure

| Metric | Value |
|--------|------:|
| Unique customers | 96,096 |
| Total orders | 99,441 |
| Total order lines | 112,650 |
| Repeat customer rate (>1 order) | 3.1% |
| Order lines per order (median) | 1.0 |

**Interpretation:** Low repeat rate means Customer × Month is effectively near order-level for most customers. Prefer order-level interpretation for decision claims.

---

## 4. Mapping to Cost-to-Serve Framework

| Cost Pool | Observed Drivers | Notes |
|-----------|------------------|-------|
| Order Handling | # orders, # order lines | Strong |
| Distribution | Freight value, weight, geo | Excellent (freight is proxy) |
| Warehousing | Weight, volume (L×H×W) | Strong |
| Returns & Waste | Canceled / unavailable status | Adequate (proxy) |

Pool sizes themselves remain **Modeled**.

---

## 5. Limitations Explicitly Recorded

1. **Low repeat purchase rate (3.1%)** — customer lifetime view is limited.
2. **No explicit quantity column** — each order_item row = one unit.
3. **No true physical return quantity** — only cancellation / unavailable status.
4. **No actual accounting cost data** — all pool totals are Modeled.
5. **Currency is BRL** — no FX conversion applied.

---

## 6. Gate Decision

**ACCEPT OLIST.**

Aligned with the project’s “public transactional backbone + explicitly modeled cost layer” strategy.

*Report generated as part of Customer Contribution After Cost-to-Serve Dataset Gate.*

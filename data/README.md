# Data Directory

## Raw

`raw/olist/` contains the original Olist Brazilian E-Commerce Public Dataset CSVs (frozen after Dataset Gate acceptance on 2026-10-02).

Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
License: CC BY-NC-SA 4.0 (see original Kaggle page)

Files:
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_customers_dataset.csv
- olist_products_dataset.csv
- olist_order_payments_dataset.csv
- olist_sellers_dataset.csv
- olist_geolocation_dataset.csv
- olist_order_reviews_dataset.csv
- product_category_name_translation.csv

Do not modify files in `raw/`. All cleaning and enrichment occurs in the pipeline and is written to `processed/`.

## Processed

Will contain:
- cleaned order-line table
- customer-month aggregates
- cost allocation tables
- robustness and scenario outputs

## Classification Hierarchy (Customer Contribution After Cost-to-Serve)

- **Tier 1 – Observed**: fields directly from these CSVs
- **Tier 2 – Derived**: calculated from observed (e.g., delivery days, volume, order frequency)
- **Tier 3 – Modeled**: product variable cost %, cost-pool sizes, allocation rates, avoidability
- **Tier 4 – Scenario**: commercial terms and service-model changes

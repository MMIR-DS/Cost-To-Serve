"""
Build cleaned order-line table (base analytical grain) from Olist raw data.
Output: data/processed/order_line.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "olist"
PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)


def load_raw():
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv")
    cat = pd.read_csv(RAW / "product_category_name_translation.csv")
    return orders, items, customers, products, sellers, cat


def build_order_line():
    from src.ingestion.download_olist import ensure_olist_data
    ensure_olist_data()

    orders, items, customers, products, sellers, cat = load_raw()

    df = items.merge(orders, on="order_id", how="left", validate="m:1")
    df = df.merge(customers, on="customer_id", how="left", validate="m:1")
    df = df.merge(
        products[
            [
                "product_id",
                "product_category_name",
                "product_weight_g",
                "product_length_cm",
                "product_height_cm",
                "product_width_cm",
            ]
        ],
        on="product_id",
        how="left",
        validate="m:1",
    )
    df = df.merge(
        sellers[["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]],
        on="seller_id",
        how="left",
        validate="m:1",
    )
    df = df.merge(cat, on="product_category_name", how="left", validate="m:1")

    df["purchase_date"] = df["order_purchase_timestamp"].dt.date
    df["purchase_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["purchase_year"] = df["order_purchase_timestamp"].dt.year
    df["purchase_year_month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    df["quantity"] = 1
    df["volume_cm3"] = (
        df["product_length_cm"].fillna(0)
        * df["product_height_cm"].fillna(0)
        * df["product_width_cm"].fillna(0)
    )

    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["is_delivered"] = df["order_status"] == "delivered"
    df["is_canceled"] = df["order_status"].isin(["canceled", "unavailable"])
    df["is_return_like"] = df["is_canceled"]

    df["gross_sales"] = df["price"] * df["quantity"]
    df["freight_value"] = df["freight_value"].fillna(0.0)
    df["product_category"] = df["product_category_name_english"].fillna(
        df["product_category_name"]
    ).fillna("unknown")

    cols = [
        "order_id", "order_item_id", "customer_id", "customer_unique_id",
        "product_id", "seller_id",
        "order_purchase_timestamp", "purchase_date", "purchase_month",
        "purchase_year_month", "order_status", "order_delivered_customer_date",
        "order_estimated_delivery_date", "delivery_days",
        "quantity", "price", "gross_sales", "freight_value",
        "product_category", "product_weight_g", "product_length_cm",
        "product_height_cm", "product_width_cm", "volume_cm3",
        "customer_zip_code_prefix", "customer_city", "customer_state",
        "seller_zip_code_prefix", "seller_city", "seller_state",
        "is_delivered", "is_canceled", "is_return_like",
    ]
    df = df[cols].copy()
    df["has_valid_price"] = df["price"] > 0
    df["has_weight"] = df["product_weight_g"].notna() & (df["product_weight_g"] > 0)

    out_path = PROCESSED / "order_line.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} order lines → {out_path}")
    return df


if __name__ == "__main__":
    build_order_line()

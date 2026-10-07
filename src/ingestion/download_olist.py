"""
Download Olist Brazilian E-Commerce CSVs if missing.

Official source (preferred): https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Automation fallback: public GitHub mirror. Row counts + SHA256 verified after download.

License: CC BY-NC-SA 4.0 — attribute Olist / Kaggle; non-commercial share-alike.
"""
from __future__ import annotations

from pathlib import Path
import urllib.request
import sys
import hashlib

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "olist"

REQUIRED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

OPTIONAL_FILES = [
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_geolocation_dataset.csv",
]

EXPECTED_ROWS = {
    "olist_orders_dataset.csv": 99441,
    "olist_order_items_dataset.csv": 112650,
    "olist_customers_dataset.csv": 99441,
    "olist_products_dataset.csv": 32951,
    "olist_sellers_dataset.csv": 3095,
    "product_category_name_translation.csv": 71,
}

EXPECTED_SHA256 = {
    "olist_orders_dataset.csv": "8df58ef3d2d7e9944010f7beecd9b75367f5588ec6e3c91cec19ae3345ef9ecf",
    "olist_order_items_dataset.csv": "0bc4d068c4fe38cbb01bd90e8746e3c613fe7b4baef75fab7b0e329701c3e279",
    "olist_customers_dataset.csv": "983a422239e1712ded753b3bf9ecf47dc73f144d306029dcfa99e70a226883d2",
    "olist_products_dataset.csv": "3e6569628a17fbc75fd206ee357b59e20364b9afa90f5b6cd5b4d624c58aa9cc",
    "olist_sellers_dataset.csv": "1f643d2b950373b85735e7794b20986f528d7a000432e7c6f9bcbb44d0846a0e",
    "product_category_name_translation.csv": "a81f0d1f27b27e7293f761bc79e3ce8f348ee39c4b3ed3e49bde38f478586278",
}

GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/HarshGupta-DS/E-Commerce_Analysis/main"
)
OFFICIAL_KAGGLE = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"


def missing_required(raw_dir: Path = RAW_DIR) -> list[str]:
    return [f for f in REQUIRED_FILES if not (raw_dir / f).exists()]


def data_ready(raw_dir: Path = RAW_DIR) -> bool:
    return len(missing_required(raw_dir)) == 0


def count_csv_rows(path: Path) -> int:
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f) - 1


def verify_row_counts(raw_dir: Path = RAW_DIR, strict: bool = True) -> dict:
    report = {}
    for name, expected in EXPECTED_ROWS.items():
        path = raw_dir / name
        if not path.exists():
            continue
        actual = count_csv_rows(path)
        report[name] = (actual, expected)
        if actual != expected:
            msg = f"Row count mismatch {name}: got {actual}, expected {expected}"
            if strict:
                raise RuntimeError(msg)
            print(f"  WARNING: {msg}")
        else:
            print(f"  OK rows {name}: {actual:,}")
        exp_hash = EXPECTED_SHA256.get(name)
        if exp_hash:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != exp_hash:
                msg = f"SHA256 mismatch {name}: got {digest[:16]}… expected {exp_hash[:16]}…"
                if strict:
                    raise RuntimeError(msg)
                print(f"  WARNING: {msg}")
            else:
                print(f"  OK hash {name}")
    return report


def _download(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {dest.name} …")
    req = urllib.request.Request(url, headers={"User-Agent": "cost-to-serve-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as out:
        out.write(resp.read())
    print(f"    → {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def ensure_olist_data(raw_dir: Path = RAW_DIR, include_optional: bool = False) -> Path:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = list(REQUIRED_FILES)
    if include_optional:
        files += [f for f in OPTIONAL_FILES if not (raw_dir / f).exists()]
    to_get = [f for f in files if not (raw_dir / f).exists()]

    if to_get:
        print(f"Missing {len(to_get)} file(s). Downloading from public mirror…")
        print(f"Official source (preferred): {OFFICIAL_KAGGLE}")
        for name in to_get:
            url = f"{GITHUB_RAW_BASE}/{name}"
            try:
                _download(url, raw_dir / name)
            except Exception as e:
                print(f"  FAILED {name}: {e}", file=sys.stderr)
        still = missing_required(raw_dir)
        if still:
            raise RuntimeError(
                "Could not download required files:\n  "
                + "\n  ".join(still)
                + f"\n\nManual: download from {OFFICIAL_KAGGLE} into data/raw/olist/"
            )
    else:
        print(f"Olist data already present in {raw_dir}")

    print("Verifying row counts vs official Olist release…")
    verify_row_counts(raw_dir, strict=True)
    print(f"Olist data ready at {raw_dir}")
    return raw_dir


if __name__ == "__main__":
    ensure_olist_data(include_optional="--optional" in sys.argv)

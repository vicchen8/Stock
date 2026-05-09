from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PRICE_FOLDER = Path("stocks_price")
STOCK_COLUMNS = ["股票代碼", "股票名稱"]


@dataclass(frozen=True)
class Condition:
    key: str
    label: str


CONDITIONS = {
    "price_above_ma5": Condition("price_above_ma5", "價格高於 5MA"),
    "price_above_ma10": Condition("price_above_ma10", "價格高於 10MA"),
    "price_above_ma20": Condition("price_above_ma20", "價格高於 20MA"),
    "price_above_ma60": Condition("price_above_ma60", "價格高於 60MA"),
    "price_above_middle": Condition("price_above_middle", "價格高於布林中線"),
    "price_below_middle": Condition("price_below_middle", "價格低於中線"),
    "volume_above_10m": Condition("volume_above_10m", "成交量大於 1000 萬"),
}


def _iter_price_files() -> list[Path]:
    if not PRICE_FOLDER.exists():
        return []
    return sorted(PRICE_FOLDER.glob("*.csv"))


def _parse_stock_file_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "_" not in stem:
        return stem, ""
    return stem.split("_", 1)


def _load_stock_data(price_file: Path) -> pd.DataFrame:
    stock = pd.read_csv(price_file, header=None)
    if stock.empty:
        return stock

    if stock.shape[1] >= 12:
        stock = stock.iloc[:, :12].copy()
        stock.columns = [
            "Date",
            "Price",
            "Volume",
            "Upper",
            "Middle",
            "Lower",
            "K",
            "D",
            "MA5",
            "MA10",
            "MA20",
            "MA60",
        ]
        return stock

    if stock.shape[1] < 3:
        return pd.DataFrame()

    stock = stock.iloc[:, :3].copy()
    stock.columns = ["Date", "Price", "Volume"]
    stock["Price"] = pd.to_numeric(stock["Price"], errors="coerce")
    stock["Volume"] = pd.to_numeric(stock["Volume"], errors="coerce")

    stock["Middle"] = stock["Price"].rolling(window=30).mean()
    stock["MA5"] = stock["Price"].rolling(window=5).mean()
    stock["MA10"] = stock["Price"].rolling(window=10).mean()
    stock["MA20"] = stock["Price"].rolling(window=20).mean()
    stock["MA60"] = stock["Price"].rolling(window=60).mean()
    return stock


def _get_last_value(stock: pd.DataFrame, column_name: str):
    return stock[column_name].iloc[-1]


def _passes_condition(stock: pd.DataFrame, condition_key: str) -> bool:
    last_price = _get_last_value(stock, "Price")
    last_volume = _get_last_value(stock, "Volume")
    last_middle = _get_last_value(stock, "Middle")

    if condition_key == "price_above_ma5":
        last_value = _get_last_value(stock, "MA5")
    elif condition_key == "price_above_ma10":
        last_value = _get_last_value(stock, "MA10")
    elif condition_key == "price_above_ma20":
        last_value = _get_last_value(stock, "MA20")
    elif condition_key == "price_above_ma60":
        last_value = _get_last_value(stock, "MA60")
    elif condition_key == "price_above_middle":
        last_value = last_middle
    elif condition_key == "price_below_middle":
        last_value = last_middle
    elif condition_key == "volume_above_10m":
        return pd.notna(last_volume) and last_volume >= 10_000_000
    else:
        raise KeyError(f"Unknown condition: {condition_key}")

    if condition_key == "price_below_middle":
        return pd.notna(last_value) and pd.notna(last_price) and last_price <= last_value

    return pd.notna(last_value) and pd.notna(last_price) and last_price >= last_value


def filter_stocks(enabled_conditions: Iterable[str] | None = None) -> pd.DataFrame:
    enabled_conditions = list(enabled_conditions or [])

    passed_rows = []
    for price_file in _iter_price_files():
        code, name = _parse_stock_file_name(price_file)

        try:
            stock = _load_stock_data(price_file)
            if stock.empty:
                continue

            if all(_passes_condition(stock, condition_key) for condition_key in enabled_conditions):
                passed_rows.append({"股票代碼": code, "股票名稱": name})
        except Exception:
            continue

    return pd.DataFrame(passed_rows, columns=STOCK_COLUMNS)


def filter() -> None:
    filter_stocks(CONDITIONS.keys())


if __name__ == "__main__":
    filter()

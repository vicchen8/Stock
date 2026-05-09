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
    "price_above_middle": Condition("price_above_middle", "價格高於中線"),
    "volume_above_10m": Condition("volume_above_10m", "成交量大於 1000 萬"),
}


def _get_last_value(stock: pd.DataFrame, column_index: int) -> float:
    return stock.iloc[-1, column_index]


def _passes_condition(stock: pd.DataFrame, condition_key: str) -> bool:
    last_price = _get_last_value(stock, 1)
    last_volume = _get_last_value(stock, 2)
    last_middle = _get_last_value(stock, 4)
    last_ma5 = _get_last_value(stock, 8)

    if condition_key == "price_above_ma5":
        return pd.notna(last_ma5) and pd.notna(last_price) and last_price >= last_ma5
    if condition_key == "price_above_middle":
        return pd.notna(last_middle) and pd.notna(last_price) and last_price >= last_middle
    if condition_key == "volume_above_10m":
        return pd.notna(last_volume) and last_volume >= 10_000_000
    raise KeyError(f"Unknown condition: {condition_key}")


def _iter_price_files() -> list[Path]:
    if not PRICE_FOLDER.exists():
        return []
    return sorted(PRICE_FOLDER.glob("*.csv"))


def _parse_stock_file_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "_" not in stem:
        return stem, ""
    code, name = stem.split("_", 1)
    return code, name


def filter_stocks(enabled_conditions: Iterable[str] | None = None) -> pd.DataFrame:
    enabled_conditions = list(enabled_conditions or [])

    passed_rows = []
    for price_file in _iter_price_files():
        code, name = _parse_stock_file_name(price_file)

        try:
            stock = pd.read_csv(price_file, header=None)
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

import os
import time
from pathlib import Path

import pandas as pd
import yfinance as yf


GOOD_STOCKS_FILE = Path("good_stocks.csv")
STOCKS_ID_FILE = Path("stocks_ID.csv")
PRICE_FOLDER = Path("stocks_price")


def _load_stock_list(stock_list_path: str | os.PathLike[str]) -> pd.DataFrame:
    return pd.read_csv(stock_list_path)


def _clear_old_price_files(folder: Path) -> int:
    resolved_folder = folder.resolve()
    removed = 0

    if not resolved_folder.exists():
        return 0

    for path in resolved_folder.glob("*.csv"):
        if path.is_file():
            path.unlink()
            removed += 1

    return removed


def fetch(stock_list_path: str | os.PathLike[str] = GOOD_STOCKS_FILE) -> dict:
    PRICE_FOLDER.mkdir(parents=True, exist_ok=True)
    removed_count = _clear_old_price_files(PRICE_FOLDER)
    if removed_count:
        print(f"已清除 {removed_count} 個舊股價檔案")

    stock_list_path = Path(stock_list_path)
    if not stock_list_path.exists():
        if stock_list_path == GOOD_STOCKS_FILE and STOCKS_ID_FILE.exists():
            stock_list_path = STOCKS_ID_FILE
        else:
            raise FileNotFoundError(f"找不到股票清單：{stock_list_path}")

    stock_list = _load_stock_list(stock_list_path)

    code_col = "股票代碼" if "股票代碼" in stock_list.columns else stock_list.columns[0]
    name_col = "股票名稱" if "股票名稱" in stock_list.columns else stock_list.columns[1]

    stock_list["yahoo_symbol"] = stock_list[code_col].astype(str).str.zfill(4) + ".TW"

    total = len(stock_list)
    success = 0
    failed = 0

    for index, row in stock_list.iterrows():
        code = str(row[code_col]).zfill(4)
        name = str(row[name_col])
        symbol = row["yahoo_symbol"]

        print(f"[{index + 1}/{total}] 開始抓取 {code} {name} ({symbol})")

        try:
            data = yf.download(symbol, period="250d", progress=False)

            if not data.empty:
                data.reset_index(inplace=True)
                filtered = data[["Date", "Close", "Volume"]]

                output_path = PRICE_FOLDER / f"{code}_{name}.csv"
                filtered.to_csv(output_path, header=False, index=False, encoding="utf-8-sig")

                success += 1
                print(f"  成功：已儲存 {code}_{name}.csv")
            else:
                failed += 1
                print(f"  失敗：{code} {name} 沒有資料")
        except Exception as exc:
            failed += 1
            print(f"  失敗：{code} {name} 抓取失敗 - {exc}")

        time.sleep(0.1)

    summary = {
        "total": total,
        "success": success,
        "failed": failed,
        "stock_list_path": str(stock_list_path),
    }
    print(f"抓取完成：成功 {success} 檔，失敗 {failed} 檔，共 {total} 檔")
    return summary


if __name__ == "__main__":
    fetch()

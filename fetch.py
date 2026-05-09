import pandas as pd
import yfinance as yf
import os
import time
from datetime import datetime

# 建立儲存資料的資料夾
def fetch():
    folder = "stocks_price"
    os.makedirs(folder, exist_ok=True)

    # 讀取股票清單
    stock_list = pd.read_csv("stocks_ID.csv")

    # 加上 .TW 後綴
    stock_list['yahoo_symbol'] = stock_list['股票代碼'].astype(str).str.zfill(4) + ".TW"

    # 逐一下載
    for i, row in stock_list.iterrows():
        code = row['股票代碼']
        name = row['股票名稱']
        symbol = row['yahoo_symbol']

        print(f"正在下載：{code} {name} ({symbol})")

        try:
            data = yf.download(symbol, period="250d", progress=False)

            if not data.empty:
                # 把 index(Date)變成欄位
                data.reset_index(inplace=True)

                # 只保留 Date, Close, Volume 欄位
                filtered = data[['Date', 'Close', 'Volume']]

                # 儲存為沒有欄位名稱、沒有 index 的 CSV
                output_path = f"{folder}/{code}_{name}.csv"
                filtered.to_csv(output_path, header=False, index=False, encoding='utf-8-sig')

                print(f"✅ 已儲存：{code}_{name}.csv")
            else:
                print(f"⚠️ 無資料：{code} {name}")
        except Exception as e:
            print(f"❌ 錯誤下載 {code} {name}：{e}")

        # 每次下載後暫停 1 秒，避免過度請求
        time.sleep(0.1)
if __name__ == "__main__":
    fetch()

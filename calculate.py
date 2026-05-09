import pandas as pd
import os

def calculate():
    # 設定資料夾路徑
    folder = "stocks_price"
    os.makedirs(folder, exist_ok=True)

    # 布林與 KD 參數
    n = 30         # 布林通道天數
    k_std = 3     # 布林標準差倍數
    kd_n = 22      # KD 計算天數

    # 迴圈處理每個 CSV 檔
    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(folder, filename)
            df = pd.read_csv(filepath, header=None, names=["Date", "Price", "Volume"])

            # 計算布林通道
            df["Middle"] = df["Price"].rolling(window=n).mean()
            df["Std"] = df["Price"].rolling(window=n).std()
            df["Upper"] = df["Middle"] + (k_std * df["Std"])
            df["Lower"] = df["Middle"] - (k_std * df["Std"])

            # 計算 KD 值
            low_min = df["Price"].rolling(window=kd_n).min()
            high_max = df["Price"].rolling(window=kd_n).max()
            df["RSV"] = (df["Price"] - low_min) / (high_max - low_min) * 100

            df["K"] = df["RSV"].ewm(alpha=1/3, adjust=False).mean()
            df["D"] = df["K"].ewm(alpha=1/3, adjust=False).mean()

            # 計算 MA
            df["MA5"] = df["Price"].rolling(window=5).mean()
            df["MA10"] = df["Price"].rolling(window=10).mean()
            df["MA20"] = df["Price"].rolling(window=20).mean()
            df["MA60"] = df["Price"].rolling(window=60).mean()

            # 只保留最後一行的布林與 KD 值
            df.iloc[:-1, 3:] = None

            # 移除中間計算用的 Std 與 RSV
            df = df[["Date", "Price", "Volume", "Upper", "Middle", "Lower", "K", "D", "MA5", "MA10", "MA20", "MA60"]]

            # 儲存 CSV
            output_path = os.path.join(folder, filename)
            df.to_csv(output_path, index=False, header=False)
            print(f"✅ 已處理 {filename}")
if __name__ == "__main__":
    calculate()

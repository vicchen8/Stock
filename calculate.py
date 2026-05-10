from __future__ import annotations

import os
from typing import Callable

import pandas as pd
from app_paths import writable_path


def calculate(progress_callback: Callable[[int, int], None] | None = None):
    folder = writable_path("stocks_price")
    os.makedirs(folder, exist_ok=True)

    n = 30
    k_std = 3
    kd_n = 22

    filenames = [filename for filename in os.listdir(folder) if filename.endswith(".csv")]
    total = len(filenames)

    for index, filename in enumerate(filenames):
        filepath = os.path.join(folder, filename)
        df = pd.read_csv(filepath, header=None, names=["Date", "Price", "Volume"])

        df["Middle"] = df["Price"].rolling(window=n).mean()
        df["Std"] = df["Price"].rolling(window=n).std()
        df["Upper"] = df["Middle"] + (k_std * df["Std"])
        df["Lower"] = df["Middle"] - (k_std * df["Std"])

        low_min = df["Price"].rolling(window=kd_n).min()
        high_max = df["Price"].rolling(window=kd_n).max()
        df["RSV"] = (df["Price"] - low_min) / (high_max - low_min) * 100

        df["K"] = df["RSV"].ewm(alpha=1 / 3, adjust=False).mean()
        df["D"] = df["K"].ewm(alpha=1 / 3, adjust=False).mean()

        df["MA5"] = df["Price"].rolling(window=5).mean()
        df["MA10"] = df["Price"].rolling(window=10).mean()
        df["MA20"] = df["Price"].rolling(window=20).mean()
        df["MA30"] = df["Price"].rolling(window=30).mean()
        df["MA60"] = df["Price"].rolling(window=60).mean()

        df.iloc[:-1, 3:] = None
        df = df[["Date", "Price", "Volume", "Upper", "Middle", "Lower", "K", "D", "MA5", "MA10", "MA20", "MA30", "MA60"]]

        df.to_csv(filepath, index=False, header=False)
        print(f"Calculated {filename}")

        if progress_callback is not None:
            progress_callback(index + 1, total)


if __name__ == "__main__":
    calculate()

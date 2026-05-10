from __future__ import annotations

import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable
from app_paths import writable_path


def get_tick(price):
    if price < 10:
        return Decimal("0.01")
    elif price < 50:
        return Decimal("0.05")
    elif price < 100:
        return Decimal("0.1")
    elif price < 500:
        return Decimal("0.5")
    elif price < 1000:
        return Decimal("1")
    else:
        return Decimal("5")


def round_to_tick(val):
    try:
        f = Decimal(str(val))
        tick = get_tick(f)
        rounded = (f / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick
        if rounded == rounded.to_integral():
            return str(int(rounded))
        return format(rounded.normalize(), "f")
    except Exception:
        return val


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) >= 3:
            parts[1] = round_to_tick(parts[1])
        new_lines.append(",".join(parts) + "\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Rounded {os.path.basename(filepath)}")


def rounder(progress_callback: Callable[[int, int], None] | None = None):
    folder = writable_path("stocks_price")
    filenames = [name for name in os.listdir(folder) if name.endswith(".csv")]
    total = len(filenames)

    for index, filename in enumerate(filenames):
        process_file(os.path.join(folder, filename))
        if progress_callback is not None:
            progress_callback(index + 1, total)


if __name__ == "__main__":
    rounder()

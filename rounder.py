import os
from decimal import Decimal, ROUND_HALF_UP

def get_tick(price):
    if price < 10:
        return Decimal('0.01')
    elif price < 50:
        return Decimal('0.05')
    elif price < 100:
        return Decimal('0.1')
    elif price < 500:
        return Decimal('0.5')
    elif price < 1000:
        return Decimal('1')
    else:
        return Decimal('5')

def round_to_tick(val):
    try:
        f = Decimal(str(val))
        tick = get_tick(f)
        # 除以 tick → 四捨五入到整數 → 乘回 tick
        rounded = (f / tick).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * tick
        # 移除不必要的小數
        if rounded == rounded.to_integral():
            return str(int(rounded))
        else:
            return format(rounded.normalize(), 'f')
    except:
        return val  # 非數字（如 Date）保持原樣

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 3:
            # 只處理 Close 欄
            parts[1] = round_to_tick(parts[1])
        new_lines.append(','.join(parts) + '\n')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"✅ 已處理：{os.path.basename(filepath)}")

# 主程式
def rounder():
    folder = 'stocks_price'
    for filename in os.listdir(folder):
        if filename.endswith('.csv'):
            process_file(os.path.join(folder, filename))
            
if __name__ == "__main__":
    rounder()

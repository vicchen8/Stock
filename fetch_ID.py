import requests
import pandas as pd

def get_all_twse_symbols():
    url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers)
    response.encoding = 'big5'  # 必須用 Big5 解碼

    df = pd.read_html(response.text)[0]
    df.columns = df.iloc[0]
    df = df[1:]

    # 印出欄位名確認
    print("欄位名稱：", df.columns.tolist())

    # 選取「上市」與「上櫃」的普通股票
    df = df[df['有價證券代號及名稱'].str.contains("^[0-9]{4}", regex=True)]

    df['股票代碼'] = df['有價證券代號及名稱'].str.extract(r'^(\d{4})')
    df['股票名稱'] = df['有價證券代號及名稱'].str.extract(r'^\d{4}\s+(.+)')

    df = df[['股票代碼', '股票名稱']].dropna()
    df = df.reset_index(drop=True)

    return df

# 主程式
if __name__ == "__main__":
    df_stocks = get_all_twse_symbols()
    df_stocks.to_csv("twse_stocks.csv", index=False, encoding="utf-8-sig")
    print("已儲存為 twse_stocks.csv")
    print(df_stocks.head())

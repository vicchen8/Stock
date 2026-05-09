import pandas as pd

def filter():
    df = pd.read_csv("stocks_ID.csv")
    for i, row in df.iterrows():
        code = row['股票代碼']
        name = row['股票名稱']
        try:
            stock = pd.read_csv(f"stocks_price/{code}_{name}.csv")

            #price>5ma
            if stock.iloc[-1,1] < stock.iloc[-1,8]:
                df = df.drop(i)

            #price<middle
            elif stock.iloc[-1,1] < stock.iloc[-1,4]:
                df = df.drop(i)

            elif stock.iloc[-1,2] < 10000000:
                df = df.drop(i)

        except:
            df = df.drop(i)

    output_path = f"good_stocks.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')


    
    
if __name__ == '__main__':
    filter()
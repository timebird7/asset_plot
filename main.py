import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import requests
import os
import datetime
import logging

# 📌 비공개 파일 임포트 (에러 처리 추가)
try:
    import private_assets  # 비공개 파일
except ImportError:
    private_assets = None
    logging.error("private_assets.py 파일을 찾을 수 없습니다.")


# 로그 설정
logging.basicConfig(filename='investment_errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_unique_filename(prefix, extension):
    today = datetime.datetime.today().strftime("%Y_%m_%d")
    count = 1
    while True:
        filename = f"{prefix}_{today}_{count}.{extension}"
        if not os.path.exists(filename):
            return filename
        count += 1

db_filename = get_unique_filename("investments", "db")
pie_chart_filename = get_unique_filename("pie", "jpg")

def initialize_db():
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_type TEXT NOT NULL,
                plot_type TEXT NOT NULL,
                ticker_symbol TEXT NULL,
                quantity REAL NOT NULL,
                current_price REAL,
                currency TEXT NOT NULL,
                leverage REAL
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def add_asset(asset_type, plot_type, ticker_symbol, quantity, currency, leverage, current_price=None):
    try:
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO assets (asset_type, plot_type, ticker_symbol, quantity, currency, leverage, current_price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (asset_type, plot_type, ticker_symbol, quantity, currency, leverage, current_price))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error adding asset: {e}")

def get_assets():
    try:
        conn = sqlite3.connect(db_filename)
        df = pd.read_sql("SELECT * FROM assets", conn)
        conn.close()
        return df
    except Exception as e:
        logging.error(f"Error fetching assets: {e}")
        return pd.DataFrame()

def fetch_current_price(asset_type, ticker):
    try:
        if asset_type == "stock":
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")

            # 🔹 데이터가 없을 경우 예외 처리
            if hist.empty:
                logging.warning(f"${ticker}: No price data found. Using last known price or default value.")
                return 0  # 🔥 기본값을 0 또는 마지막으로 저장된 가격으로 설정 가능
            
            return hist["Close"].iloc[-1]

        elif asset_type == "crypto":
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}USDT"
            response = requests.get(url)
            if response.status_code == 200:
                return float(response.json()["price"])

        return None

    except Exception as e:
        logging.error(f"Error fetching current price for {ticker}: {e}")
        return None

def fetch_usd_krw_exchange_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["rates"]["KRW"]
        return 1  # 기본값
    except Exception as e:
        logging.error(f"Error fetching USD-KRW exchange rate: {e}")
        return 1

def calculate_final_values(df):
    usd_krw = fetch_usd_krw_exchange_rate()
    for index, row in df.iterrows():
        try:
            if pd.isna(row["current_price"]):
                df.at[index, "current_price"] = fetch_current_price(row["asset_type"], row["ticker_symbol"])
            if row["currency"] == "USD":
                df.at[index, "current_price"] *= usd_krw
                # df.at[index, "buy_price"] *= usd_krw
        except Exception as e:
            logging.error(f"Error calculating final values for {row['ticker_symbol']}: {e}")
    df["final_value"] = (df["current_price"] * df["quantity"] * df["leverage"]).round(2)
    # df["return_rate"] = ((df["current_price"] - df["buy_price"]) / df["buy_price"]) * 100
    return df

def save_asset_distribution_chart(df):
    try:
        grouped_df = df.groupby("plot_type")["final_value"].sum().sort_values(ascending=False)  # plot_type 기준으로 합산

        plt.figure(figsize=(8, 6))
        plt.pie(grouped_df, labels=grouped_df.index, autopct='%1.1f%%', startangle=140)
        plt.title("Investment Asset Distribution by Asset Type (KRW)")
        plt.savefig(pie_chart_filename)
        plt.close()
    except Exception as e:
        logging.error(f"Error saving asset distribution chart: {e}")

# 실행 예제
initialize_db()  # DB 초기화 (최초 1회 실행)
if private_assets:
    private_assets.run_add_asset(add_asset)

# 데이터 불러오기 및 분석
assets_df = get_assets()
if not assets_df.empty:
    assets_df = calculate_final_values(assets_df)
    print(assets_df)
    # 🔹 final_value 총합 계산 후 출력
    total_value = assets_df["final_value"].sum()
    print(f"총 자산 가치: {total_value:,.2f} KRW")    
    save_asset_distribution_chart(assets_df)

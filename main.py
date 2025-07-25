import asyncio
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests


TOKEN = "YOUR_TOKEN_HERE"
BASE_URL = f"API_LINK_HERE{TOKEN}/"
CHAT_ID = "YOUR_CHAT_ID_HERE"


def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.json()


def send_file(chat_id, file_path):
    url = BASE_URL + "sendDocument"
    with open(file_path, 'rb') as file:
        payload = {"chat_id": chat_id}
        files = {"document": file}
        response = requests.post(url, data=payload, files=files)
    return response.json()


def convert_to_utc(local_time_str, local_tz_str='UTC'):
    local_tz = pytz.timezone(local_tz_str)
    local_time = local_tz.localize(datetime.strptime(local_time_str, '%Y-%m-%d %H:%M:%S'))
    return local_time.astimezone(pytz.utc)


def fetch_ohlcv(symbol, timeframe, start_date_str, end_date_str, exchange_id):
    start_date = convert_to_utc(start_date_str)
    end_date = convert_to_utc(end_date_str)
    since = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    exchange = getattr(ccxt, exchange_id)()
    
    ohlcv = []
    while since <= end_timestamp:
        data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=500)
        if not data:
            break
        ohlcv += data
        last = data[-1][0]
        if last >= end_timestamp or last == since:
            break
        since = last + 1
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df[df['timestamp'] <= pd.to_datetime(end_date_str)]


def analyze_ohlcv(data):
    if len(data) < 5:
        return "No Signal"
    
    c3, c2, c1 = data['close'].iloc[-4], data['close'].iloc[-3], data['close'].iloc[-2]
    o3, o2 = data['open'].iloc[-4], data['open'].iloc[-3]
    
    if c3 < o3 and c2 < c3 and c1 > o2:
        return "Long"
    elif c3 > o3 and c2 > c3 and c1 < o2:
        return "Short"
    else:
        return "No Signal"


async def send_report():
    exchange_id = "kucoin"  #NAME OF EXCHANGE HERE
    timeframe_daily = "1d"
    timeframe_4h = "4h"
    n_symbols = 150     #COUNT OF SYMBOLS PER EACH SCAN HERE
    

    exchange = getattr(ccxt, exchange_id)()
    symbols = [symbol for symbol in exchange.load_markets().keys() if "/USDT" in symbol]
    

    symbols = symbols[:n_symbols]
    

    now = datetime.now().strftime("%Y-%m-%d 00:00:00")
    current_date = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    start_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    results = []


    for symbol in symbols:
        try:
            print(f"Fetching data for {symbol} in 1D...")
            df_daily = fetch_ohlcv(symbol, timeframe_daily, start_date, end_date, exchange_id)
            signal_daily = analyze_ohlcv(df_daily)
            if signal_daily != "No Signal":
                print(f"Fetching data for {symbol} in 4H...")
                df_4h = fetch_ohlcv(symbol, timeframe_4h, start_date, end_date, exchange_id)
                signal_4h = analyze_ohlcv(df_4h)
                
                results.append({
                    "Symbol": symbol,
                    "Signal_Daily": signal_daily,
                    "Signal_4H": signal_4h
                })
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
    
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        print(result_df)
        
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        csv_file_path = f'output/signals_{current_time}.csv'
        
        result_df.to_csv(csv_file_path, index=False)
        print(f"Results saved to {csv_file_path}")
        
        try:
            send_message(CHAT_ID, "Report is ready. Sending the csv file... ")
            send_file(CHAT_ID, csv_file_path)
            print(f"File sent to user: {csv_file_path}")
        except Exception as e:
            print(f"Error sending file: {e}")


async def main():
    await send_report()

if __name__ == "__main__":
    asyncio.run(main())



import yfinance as yf
import talib
import numpy as np
import pandas as pd
import datetime
import requests
import time
import creds
import urllib.parse
import hashlib
import hmac
import base64

# Set start and end dates for historical data
startdate = datetime.datetime(2022, 7, 1)
enddate = datetime.datetime(2024, 1, 1)

# List of cryptocurrency symbols to be processed (Kraken format)
symbols = {
    'BTCUSD': 'XXBTZUSD',
    'ETHUSD': 'XETHZUSD',
    'XRPUSD': 'XXRPZUSD'
}

# API credentials
api_url = "https://api.kraken.com"
api_key = creds.api
api_sec = creds.secret

# Function to generate Kraken API signature
def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

# Function to make requests to Kraken API
def kraken_request(uri_path, data, api_key, api_sec):
    headers = {
        'API-Key': api_key,
        'API-Sign': get_kraken_signature(uri_path, data, api_sec)
    }
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

# Broker class to handle Kraken API interactions
class Broker:
    @staticmethod
    def OHLCdata(pair, interval='1m', candles=200):
        resp = requests.get(f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}')
        if resp.status_code != 200:
            raise Exception(f"Error fetching data from Kraken API: {resp.status_code}")
        
        data = resp.json()
        if 'error' in data and data['error']:
            raise Exception(f"Kraken API error: {data['error']}")
        if 'result' not in data:
            raise Exception("Unexpected response format from Kraken API")
        
        # Extract the OHLC data using the correct pair symbol key
        result_key = list(data['result'].keys())[0]
        ohlc_data = data['result'][result_key]
        df = pd.DataFrame(ohlc_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'vwap', 'Volume', 'Count'])
        df['Time'] = pd.to_datetime(df['Time'], unit='s')
        df.set_index('Time', inplace=True)
        return df.tail(candles)

    @staticmethod
    def cancel_all_orders():
        resp = kraken_request('/0/private/CancelAll', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    @staticmethod
    def account_balance():
        resp = kraken_request('/0/private/Balance', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    @staticmethod
    def cancel_order(txid):
        resp = kraken_request('/0/private/CancelOrder', {"nonce": str(int(1000 * time.time())), "txid": txid}, api_key, api_sec)
        return resp.json()

    @staticmethod
    def place_order(order_type='buy', volume=1, pair="XXBTZUSD", price=27500):
        resp = kraken_request('/0/private/AddOrder', {
            "nonce": str(int(1000 * time.time())),
            "ordertype": "limit",
            "type": order_type,
            "volume": volume,
            "pair": pair,
            "price": price
        }, api_key, api_sec)
        return resp.json()

# Strategy class to handle trading strategy logic
class Strategy(Broker):
    def __init__(self, ticker, startdate, enddate, capital):
        self.startdate = startdate
        self.enddate = enddate
        self.capital = capital
        self.ticker = ticker
        self.data = self.fetch_data()
        
    def fetch_data(self):
        data = Broker.OHLCdata(self.ticker)
        return data

    def add_indicators(self):
        self.data['EMA200'] = talib.EMA(self.data['Close'], timeperiod=200)
        self.data['Hammer'] = talib.CDLHAMMER(self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['MorningStar'] = talib.CDLMORNINGSTAR(self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['EveningStar'] = talib.CDLEVENINGSTAR(self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['ShootingStar'] = talib.CDLSHOOTINGSTAR(self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['MACD'], self.data['MACDSignal'], self.data['MACDHistory'] = talib.MACD(self.data['Close'], fastperiod=12, slowperiod=26)
        return self.data

    def generate_signals(self):
        self.data['Signal'] = 0
        for i in range(3, len(self.data)):
            if (self.data['Close'].iloc[i] > self.data['EMA200'].iloc[i] and self.data['MACD'].iloc[i] < self.data['MACDSignal'].iloc[i]):
                if (self.data['Hammer'].iloc[i-3] != 0 or self.data['MorningStar'].iloc[i-3] != 0) and \
                   (self.data['Close'].iloc[i-3] < self.data['Close'].iloc[i-2] or 
                    self.data['Close'].iloc[i-2] < self.data['Close'].iloc[i-1] or 
                    self.data['Close'].iloc[i-1] < self.data['Close'].iloc[i]):
                    self.data.at[i, 'Signal'] = 1
            elif (self.data['Close'].iloc[i] < self.data['EMA200'].iloc[i] and self.data['MACD'].iloc[i] > self.data['MACDSignal'].iloc[i]):
                if (self.data['EveningStar'].iloc[i] != 0 or self.data['ShootingStar'].iloc[i] != 0) and \
                   (self.data['Close'].iloc[i-3] > self.data['Close'].iloc[i-2] or 
                    self.data['Close'].iloc[i-2] > self.data['Close'].iloc[i-1] or 
                    self.data['Close'].iloc[i-1] > self.data['Close'].iloc[i]):
                    self.data.at[i, 'Signal'] = -1
        return self.data

    def execute_signals(self):
        if self.data['Signal'].iloc[-1] == 1:
            print(f"Placing Buy Order for {self.ticker}")
            self.place_order(pair=self.ticker)
        elif self.data['Signal'].iloc[-1] == -1:
            print(f"Placing Sell Order for {self.ticker}")
            self.place_order(order_type='sell', pair=self.ticker)
        else:
            print(f"No order has been placed for {self.ticker}")

# Main loop to process each symbol and wait for the next candle
while True:
    for symbol, kraken_pair in symbols.items():
            strategy = Strategy(kraken_pair, startdate, enddate, 10000)
            strategy.add_indicators()
            strategy.generate_signals()
            strategy.execute_signals()
            strategy.data.to_csv(f"{symbol}_signals.csv")
        
    
    # Sleep for 60 seconds before fetching the next 1-minute candle
    print("Sleeping for 60 seconds...")
    time.sleep(60)

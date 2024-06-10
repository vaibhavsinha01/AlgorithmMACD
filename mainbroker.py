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

startdate = datetime.datetime(2022, 7, 1)
enddate = datetime.datetime(2024, 1, 1)
stocks = ['ETHUSDT', 'BTCUSDT']

api_url = "https://api.kraken.com"
api_key = creds.api
api_sec = creds.secret

def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def kraken_request(uri_path, data, api_key, api_sec):
    headers = {
        'API-Key': api_key,
        'API-Sign': get_kraken_signature(uri_path, data, api_sec)
    }
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

class Broker:
    def OHLCdata(pair, interval='1m', candles=200):
        resp = requests.get(f'https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}')
        ohlc_data = resp.json()
        df = pd.DataFrame(ohlc_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'vwap', 'Volume', 'Count'])
        df['Time'] = pd.to_datetime(df['Time'], unit='s')
        df.set_index('Time', inplace=True)
        return df.tail(candles)

    def cancel_all_orders():
        resp = kraken_request('/0/private/CancelAll', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    def account_balance():
        resp = kraken_request('/0/private/Balance', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    def cancel_order(txid):
        resp = kraken_request('/0/private/CancelOrder', {"nonce": str(int(1000 * time.time())), "txid": txid}, api_key, api_sec)
        return resp.json()

    def place_order(order_type='buy', volume=1, pair="XBTUSD", price=27500):
        resp = kraken_request('/0/private/AddOrder', {
            "nonce": str(int(1000 * time.time())),
            "ordertype": "limit",
            "type": order_type,
            "volume": volume,
            "pair": pair,
            "price": price
        }, api_key, api_sec)
        return resp.json()

class Strategy(Broker):
    def __init__(self, ticker, startdate, enddate, capital):
        self.startdate = startdate
        self.enddate = enddate
        self.capital = capital
        self.ticker = ticker
        self.data = self.OHLCdata()

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
                    self.data['Signal'].iloc[i] = 1
            elif (self.data['Close'].iloc[i] < self.data['EMA200'].iloc[i] and self.data['MACD'].iloc[i] > self.data['MACDSignal'].iloc[i]):
                if (self.data['EveningStar'].iloc[i] != 0 or self.data['ShootingStar'].iloc[i] != 0) and \
                   (self.data['Close'].iloc[i-3] > self.data['Close'].iloc[i-2] or 
                    self.data['Close'].iloc[i-2] > self.data['Close'].iloc[i-1] or 
                    self.data['Close'].iloc[i-1] > self.data['Close'].iloc[i]):
                    self.data['Signal'].iloc[i] = -1
        return self.data

    def execute_signals(self):
        if self.data['Signal'].iloc[-1] == 1:
            print("Placing Buy Order")
            self.place_order(order_type='buy')
        elif self.data['Signal'].iloc[-1] == -1:
            print("Placing Sell Order")
            self.place_order(order_type='sell')
        elif self.data['Signal'].iloc[-1] == 0:
            print("The signal is 0 no order has been placed")
        else:
            print("Error")

for stock in stocks:
    while True:
        strategy = Strategy(stock, startdate, enddate, 10000)
        strategy.OHLCdata(interval='1m',candles=200)
        strategy.add_indicators()
        strategy.generate_signals()
        strategy.execute_signals()
        strategy.data.to_csv(f"{stock}_signals.csv")
time.sleep(60)

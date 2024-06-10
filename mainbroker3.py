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
stock='ETHUSDT'

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

class Strategy:
    def __init__(self, ticker, startdate, enddate, capital):
        self.startdate = startdate
        self.enddate = enddate
        self.capital = capital
        self.ticker = ticker
        self.data = None

    def OHLCdata(self):
        resp = requests.get('https://api.kraken.com/0/public/OHLC?pair=XBTUSD')
        a=resp.json()
        self.data = pd.DataFrame(a['result']['XXBTZUSD'],columns=['Time','Open','High','Low','Close','vwap','Volume','count'])
        return self.data

    def cancel_all_orders(self):
        resp = kraken_request('/0/private/CancelAll', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    def account_balance(self):
        resp = kraken_request('/0/private/Balance', {"nonce": str(int(1000 * time.time()))}, api_key, api_sec)
        return resp.json()

    def place_order(self,order_type='buy', volume=1, pair="XXBTZUSD", price=27500):
        resp = kraken_request('/0/private/AddOrder', {
            "nonce": str(int(1000 * time.time())),
            "ordertype": "limit",
            "type": order_type,
            "volume": volume,
            "pair": pair,
            "price": price
        }, api_key, api_sec)
        return resp.json()

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
        for i in range(300, len(self.data)):
            if (float(self.data['Close'].iloc[i]) > float(self.data['EMA200'].iloc[i]) and self.data['MACD'].iloc[i] < self.data['MACDSignal'].iloc[i]):
                if (self.data['Hammer'].iloc[i-3] != 0 or self.data['MorningStar'].iloc[i-3] != 0) and \
                   (self.data['Close'].iloc[i-3] < self.data['Close'].iloc[i-2] or 
                    self.data['Close'].iloc[i-2] < self.data['Close'].iloc[i-1] or 
                    self.data['Close'].iloc[i-1] < self.data['Close'].iloc[i]):
                    self.data.at[i, 'Signal'] = 1
            elif (float(self.data['Close'].iloc[i]) < float(self.data['EMA200'].iloc[i]) and self.data['MACD'].iloc[i] > self.data['MACDSignal'].iloc[i]):
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


strategy = Strategy(stock, startdate, enddate, 10000)
strategy.OHLCdata()
strategy.add_indicators()
strategy.generate_signals()
strategy.execute_signals()

# working till dataframe and function apply just def main function is needed.

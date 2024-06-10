from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import talib
import numpy as np
import pandas as pd

class MACDPATTERN(Strategy):
    stlo = 95  
    tkpr = 105  

    def __init__(self):
        self.data['EMA200'] = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.data['Hammer'] = self.I(lambda o, h, l, c: talib.CDLHAMMER(o, h, l, c), 
                             self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['MorningStar'] = self.I(lambda o, h, l, c: talib.CDLMORNINGSTAR(o, h, l, c), 
                                  self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['EveningStar'] = self.I(lambda o, h, l, c: talib.CDLEVENINGSTAR(o, h, l, c), 
                                  self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['ShootingStar'] = self.I(lambda o, h, l, c: talib.CDLSHOOTINGSTAR(o, h, l, c), 
                                   self.data['Open'], self.data['High'], self.data['Low'], self.data['Close'])
        self.data['MACD'], self.data['MACDSignal'], _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26)

    def next(self):
        if (self.data['EMA200'] > self.data['Close'] and self.data['MACD'] < self.data['MACDSignal'] and self.data['Close'].iloc[-2]<self.data['Close'].iloc[-1]<self.data['Close'].iloc[0]):
            if (self.data['Hammer'].iloc[-3] != 0 or self.data['MorningStar'].iloc[-3] != 0):
                self.position.close()
                self.buy(sl=(self.stlo * self.data.Close) / 100, tp=(self.tkpr * self.data.Close) / 100)
        elif (self.data['EMA200'] < self.data['Close'] and self.data['MACD'] > self.data['MACDSignal'] and self.data['Close'].iloc[-2]>self.data['Close'].iloc[-1]>self.data['Close'].iloc[0]):
            if (self.data['EveningStar'].iloc[-3] != 0 or self.data['ShootingStar'].iloc[-3] != 0):
                self.position.close()
                self.sell(sl=(self.tkpr * self.data.Close) / 100, tp=(self.stlo * self.data.Close) / 100)

def main():
    bt = Backtest(GOOG, MACDPATTERN, cash=10000)
    stats = bt.run()
    print(stats)
    bt.plot()

if __name__ == "__main__":
    main()

#the changes to be made is to compare the third last candle
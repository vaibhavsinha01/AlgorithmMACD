from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import talib
import numpy as np
import pandas as pd

class MACDPATTERN(Strategy):
    stlo = 95  
    tkpr = 105  

    def init(self):
        self.EMA200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.Hammer = self.I(lambda o, h, l, c: talib.CDLHAMMER(o, h, l, c), 
                             self.data.Open, self.data.High, self.data.Low, self.data.Close)
        self.MorningStar = self.I(lambda o, h, l, c: talib.CDLMORNINGSTAR(o, h, l, c), 
                                  self.data.Open, self.data.High, self.data.Low, self.data.Close)
        self.EveningStar = self.I(lambda o, h, l, c: talib.CDLEVENINGSTAR(o, h, l, c), 
                                  self.data.Open, self.data.High, self.data.Low, self.data.Close)
        self.ShootingStar = self.I(lambda o, h, l, c: talib.CDLSHOOTINGSTAR(o, h, l, c), 
                                   self.data.Open, self.data.High, self.data.Low, self.data.Close)
        self.MACD, self.MACDSignal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26)

    def next(self):
        if (self.EMA200 > self.data.Close and self.MACD < self.MACDSignal):
            if (self.Hammer != 0 or self.MorningStar != 0):
                self.position.close()
                self.buy(sl=(self.stlo * self.data.Close) / 100, tp=(self.tkpr * self.data.Close) / 100)
        elif (self.EMA200 < self.data.Close and self.MACD > self.MACDSignal):
            if (self.EveningStar != 0 or self.ShootingStar != 0):
                self.position.close()
                self.sell(sl=(self.tkpr * self.data.Close) / 100, tp=(self.stlo * self.data.Close) / 100)

def main():
    bt = Backtest(GOOG, MACDPATTERN, cash=10000)
    stats = bt.run()
    print(stats)
    bt.plot()

if __name__ == "__main__":
    main()

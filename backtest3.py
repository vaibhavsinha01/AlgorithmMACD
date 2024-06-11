from backtesting import Backtest, Strategy
from backtesting.test import GOOG
import talib

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
        if len(self.data.Close) < 4:  
            return -1
        #the iloc function isn't working
        if (self.EMA200[-1] > self.data.Close[-1] and 
            self.MACD[-1] < self.MACDSignal[-1] and 
            self.data.Close[-3] < self.data.Close[-2] < self.data.Close[-1]):
            if (self.Hammer[-3] != 0 or self.MorningStar[-3] != 0):
                self.position.close()
                self.buy(sl=(self.stlo * self.data.Close[-1]) / 100, tp=(self.tkpr * self.data.Close[-1]) / 100)
        elif (self.EMA200[-1] < self.data.Close[-1] and 
              self.MACD[-1] > self.MACDSignal[-1] and 
              self.data.Close[-3] > self.data.Close[-2] > self.data.Close[-1]):
            if (self.EveningStar[-3] != 0 or self.ShootingStar[-3] != 0):
                self.position.close()
                self.sell(sl=(self.tkpr * self.data.Close[-1]) / 100, tp=(self.stlo * self.data.Close[-1]) / 100)

def main():
    bt = Backtest(GOOG, MACDPATTERN, cash=10000)
    stats = bt.run()
    print(stats)
    bt.plot()
    st=bt.optimize(
        stlo=range(90, 99, 1),
        tkpr=range(101, 110, 1),
        maximize='Win Rate [%]'
    )
    print(st)

if __name__ == "__main__":
    main()

#working but not sure how properly
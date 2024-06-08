# i will make a reversal indicator 
# this will give you the probablity of reversal using candlestick patterns and current state of indicators
# here both 1 and -1 are present so it is working
# yup working for the code
import yfinance as yf
import talib
import numpy
import pandas
import datetime

#first we will make a function to fetchdata
startdate=datetime.datetime(2022,7,1)
enddate=datetime.datetime(2024,1,1)

class Strategy:
    def __init__(self,ticker,startdate,enddate,capital):
        self.startdate=startdate
        self.enddate=enddate
        self.capital=capital
        self.ticker=ticker
        self.data=None

    def Fetchdata(self):
        self.data=yf.download(self.ticker,start=self.startdate,end=self.enddate,interval='1h')
        self.data.drop('Adj Close',axis=1,inplace=True)
        return self.data
    
    #here there will be a function to check the possible reversal candles using the talib and also it will check with the rsi divergence 
    #and also the macd operator and the ema20 and ema50 comparision
    def Functions(self):
        self.data['EMA200']=talib.EMA(self.data['Close'],timeperiod=200)
        self.data['Hammer']=talib.CDLHAMMER(self.data['Open'],self.data['High'],self.data['Low'],self.data['Close'])
        self.data['MorningStar']=talib.CDLMORNINGSTAR(self.data['Open'],self.data['High'],self.data['Low'],self.data['Close'])
        self.data['EveningStar']=talib.CDLEVENINGSTAR(self.data['Open'],self.data['High'],self.data['Low'],self.data['Close'])
        self.data['ShootingStar']=talib.CDLSHOOTINGSTAR(self.data['Open'],self.data['High'],self.data['Low'],self.data['Close'])
        self.data['MACD'],self.data['MACDSignal'],self.data['MACDHistory']=talib.MACD(self.data['Close'],fastperiod=12,slowperiod=26)
        return self.data
    
    def Signal(self):
        self.data['Signal']=0
        for i in range(len(self.data)):
            if(self.data['Close'].iloc[i]>self.data['EMA200'].iloc[i] and self.data['MACD'].iloc[i]<self.data['MACDSignal'].iloc[i]):
                if(self.data['Hammer'].iloc[i-3]!=0 or self.data['MorningStar'].iloc[i-3]!=0) and (self.data['Close'].iloc[i-3]<self.data['Close'].iloc[i-2] or self.data['Close'].iloc[i-2]<self.data['Close'].iloc[i-1] or self.data['Close'].iloc[i-1]<self.data['Close'].iloc[i]):
                    self.data['Signal'].iloc[i]=1
                else:
                    self.data['Signal'].iloc[i]=0
            elif(self.data['Close'].iloc[i]<self.data['EMA200'].iloc[i] and self.data['MACD'].iloc[i]>self.data['MACDSignal'].iloc[i]):
                if(self.data['EveningStar'].iloc[i]!=0 or self.data['ShootingStar'].iloc[i]!=0) and (self.data['Close'].iloc[i-3]>self.data['Close'].iloc[i-2] or self.data['Close'].iloc[i-2]>self.data['Close'].iloc[i-1]  or self.data['Close'].iloc[i-1]>self.data['Close'].iloc[i]):
                    self.data['Signal'].iloc[i]=-1
                else:
                    self.data['Signal'].iloc[i]=0
            else:
                self.data['Signal'].iloc[i]=0
        self.data.to_csv("file.csv")
        return self.data
    
    def ProfitLoss(self):
        capital=10000
        profit=0
        quantity=0
        for i in range(len(self.data)):
            if(self.data['Signal'].iloc[i]==1 or self.data['Signal'].iloc[i]==-1):
                quantity=capital/self.data['Close'].iloc[i]
                profit=(self.data['Close'].iloc[i+15]-self.data['Close'].iloc[i])*self.data['Signal'].iloc[i]*quantity
                capital=capital+profit
        print(self.data)
        print(capital)

        #the strategy will be to sell this after 15 candles
stocks=['NVDA','GOOGL','MSFT','META','JPM','RELIANCE.NS']
for stock in stocks:
    strategy=Strategy(stock,startdate,enddate,'10000')
    strategy.Fetchdata()
    strategy.Functions()
    strategy.Signal()
    strategy.ProfitLoss()
            
import backtrader as bt
import yfinance as yf
import numpy as np

class VolumeStrategy(bt.Strategy):
    def __init__(self, params):
        self.dataclose = self.datas[0].close
        self.datavol = self.datas[0].volume
        self.period = float(params[1])
        self.sma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.period)
        self.bollinger = bt.indicators.BollingerBands(self.dataclose, period=self.period, devfactor=2.0)
        self.obv = [0]  # Initialize OBV as a list to store the cumulative OBV
        self.position_size = float(params[0])

    def next(self):
        # Calculate OBV (On-Balance Volume)
        if self.dataclose[0] > self.dataclose[-1]:
            self.obv.append(self.obv[-1] + self.datavol[0])
        elif self.dataclose[0] < self.dataclose[-1]:
            self.obv.append(self.obv[-1] - self.datavol[0])
        else:
            self.obv.append(self.obv[-1])  # No price change, OBV stays the same

        # Trading logic based on OBV and Bollinger Bands
        if self.obv[-1] > self.sma[0] and self.dataclose[0] > self.bollinger.lines.bot:
            if self.position.size == 0:
                self.buy(size=self.position_size)
        elif self.obv[-1] < self.sma[0] and self.dataclose[0] < self.bollinger.lines.top:
            if self.position.size > 0:
                self.sell(size=self.position_size)

        # Stop loss logic
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.position_size / 100)):
            self.close()

def runStrategy(params):
    cerebro = bt.Cerebro()

    cerebro.broker.set_cash(1000)
    data = yf.download("SPY")
    bt_data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(bt_data)
    
    cerebro.addstrategy(VolumeStrategy(params))
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='myret')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='mysqn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydd')
    
    strat = cerebro.run()[0]
    
    final_portfolio_value = cerebro.broker.getvalue()
    final_cash = cerebro.broker.get_cash()
    annual_return = strat.analyzers.myret.get_analysis()
    sharpe_ratio = strat.analyzers.mysharpe.get_analysis()["sharperatio"]
    sqn = strat.analyzers.mysqn.get_analysis()["sqn"]
    drawdown = strat.analyzers.mydd.get_analysis()["drawdown"]
    total = 0
    count = 0
    for key, value in annual_return.items():
        total += value
        count += 1
    
    total /= count
    total += 1
    # Return as a formatted string
    return f"""
    Initial Cash: 1000

    Final Portfolio Value: {final_portfolio_value:.2f}

    Final Cash: {final_cash:.2f}

    Annual Return: {total}

    Sharpe Ratio: {sharpe_ratio}

    SQN: {sqn}

    DrawDown: {drawdown}
    """




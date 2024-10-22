import backtrader as bt
import yfinance as yf
import numpy as np

class Arbitrage(bt.Strategy):
    def __init__(self, params):
        # Data for the two assets
        self.dataclose1 = self.datas[0].close  # Asset 1
        self.dataclose2 = self.datas[1].close  # Asset 2
        self.spread_threshold = float(params[0])
        self.position_size = int(params[1])
        # Calculate the price spread between the two assets
        self.price_spread = self.dataclose1 - self.dataclose2

        # Moving average of the spread to determine the baseline (mean-reverting assumption)
        self.spread_ma = bt.indicators.SimpleMovingAverage(self.price_spread, period=20)
        self.stop_loss = int(input("Enter the stop loss: "))
        
    def next(self):
        # Calculate the current price spread
        current_spread = self.dataclose1[0] - self.dataclose2[0]
        mean_spread = self.spread_ma[0]
        
        # Check if the spread has deviated significantly from the mean
        if current_spread > mean_spread * (1 + self.spread_threshold):
            # If the spread is too high, sell the more expensive asset (1) and buy the cheaper asset (2)
            if not self.getposition(self.datas[0]).size:  # No position in Asset 1
                self.sell(data=self.datas[0], size=self.position_size)  # Short Asset 1
            if not self.getposition(self.datas[1]).size:  # No position in Asset 2
                self.buy(data=self.datas[1], size=self.position_size)   # Long Asset 2
        elif current_spread < mean_spread * (1 - self.spread_threshold):
            # If the spread is too low, buy the more expensive asset (1) and sell the cheaper asset (2)
            if not self.getposition(self.datas[0]).size:
                self.buy(data=self.datas[0], size=self.position_size)  # Long Asset 1
            if not self.getposition(self.datas[1]).size:
                self.sell(data=self.datas[1], size=self.position_size)  # Short Asset 2
        
        # Exit strategy: close positions when the spread reverts back to the mean
        if abs(current_spread - mean_spread) < mean_spread * 0.01:  # Close if near mean spread
            self.close(data=self.datas[0])
            self.close(data=self.datas[1])

        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.stop_loss / 100)):
            self.close()

def runStrategy(params):
    cerebro = bt.Cerebro()

    cerebro.broker.set_cash(1000)

    # Download data for two related assets (e.g., SPY and QQQ for US stocks)
    data1 = yf.download("SPY")
    bt_data1 = bt.feeds.PandasData(dataname=data1)
    cerebro.adddata(bt_data1)

    data2 = yf.download("NDAQ")
    bt_data2 = bt.feeds.PandasData(dataname=data2)
    cerebro.adddata(bt_data2)

    # Add the arbitrage strategy
    cerebro.addstrategy(Arbitrage(params))

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



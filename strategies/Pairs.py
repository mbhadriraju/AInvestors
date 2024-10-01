import backtrader as bt
import yfinance as yf

class Pairs(bt.Strategy):
    params = (
        ('deviation', float(input("Enter the Standard Deviation Factor: "))),
        ('fast_period', int(input("Enter the fast moving average period (Enter 1 for current price): "))),
        ('slow_period', int(input("Enter the slow moving average period: "))),
        ('stop_loss', int(input("Enter the stop loss: "))),
        ('position_size', int(input("Enter the position size: "))) 
    )

    def __init__(self):
        self.dataclose1 = self.datas[0].close
        self.dataclose2 = self.datas[1].close
        self.diff = self.dataclose1 - self.dataclose2  # Calculate the difference
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.diff, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.diff, period=self.p.slow_period)
        self.boll_bands = bt.indicators.BBands(self.diff, period=self.p.slow_period, devfactor=self.p.deviation)

    def next(self):
        # Calculate the latest values
        fast_ma_value = self.fast_ma[0]
        boll_bot_value = self.boll_bands.bot[0]
        boll_top_value = self.boll_bands.top[0]

        # Check for buy signal
        if fast_ma_value < boll_bot_value:
            if not self.position:  # Check if not in position
                self.buy(size=self.p.position_size)

        # Check for sell signal
        elif fast_ma_value > boll_top_value:
            if not self.position:  # Check if not in position
                self.sell(size=self.p.position_size)

        # Global stop-loss check
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.p.stop_loss / 100)):
            self.close()  # Close all positions if stop loss is triggered

def runStrategy():
    cerebro = bt.Cerebro()

    cerebro.broker.set_cash(1000)

    # Downloading data for MSFT and AAPL
    data1 = yf.download("MSFT", period="1y")
    data2 = yf.download("AAPL", period="1y")

    bt_data1 = bt.feeds.PandasData(dataname=data1)
    bt_data2 = bt.feeds.PandasData(dataname=data2)

    cerebro.adddata(bt_data1)
    cerebro.adddata(bt_data2)
    
    cerebro.addstrategy(Pairs)
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

    # Return as a formatted string
    return f"""
    Final Portfolio Value: {final_portfolio_value:.2f}
    Final Cash: {final_cash:.2f}

    Annual Return: {annual_return}

    Sharpe Ratio: {sharpe_ratio}
    SQN: {sqn}
    DrawDown: {drawdown}
    """

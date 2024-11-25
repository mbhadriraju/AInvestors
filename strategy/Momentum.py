import backtrader as bt
import yfinance as yf

class momentum(bt.Strategy):
    params = (
        ('RSItest', True),
        ('MACDtest', True),
        ('stoploss', 5.0),
        ('threshigh', 70),
        ('threshlow', 30),
        ('short_period', 10),
        ('long_period', 30),
        ('positionsize', 100),  # Size of the position in units of the asset's price
    )
    def __init__(self):
        self.dataclose = self.datas[0].close
        # Trend-following indicators (Moving Averages)
        self.short_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.params.long_period)

        if self.params.RSItest == True:
            self.rsi = bt.indicators.RSI(self.dataclose, period=self.params.short_period)
        if self.params.MACDtest == True:
            self.macd = bt.indicators.MACD(self.dataclose, period_me1=self.params.short_period, 
                                           period_me2=self.params.long_period, 
                                           period_signal=int((self.params.long_period + self.params.short_period) / 2))

    def next(self):
        rsi_value = self.rsi[0] if self.params.RSItest else None
        macd_value = self.macd[0] if self.params.MACDtest else None
        macd_signal = self.macd.signal[0] if self.params.MACDtest else None

        # Trend-following buy signal: short MA crosses above long MA
        if self.short_ma > self.long_ma:
            if self.position.size < self.params.positionsize:
                self.buy()

        # Trend-following sell signal: short MA crosses below long MA
        elif self.short_ma < self.long_ma:
            if self.position.size * -1 < self.params.positionsize:
                self.sell()

        # Optional indicators (RSI/MACD)
        if self.params.RSItest and rsi_value is not None:
            if rsi_value > self.params.threshigh:
                self.sell()
            elif rsi_value < self.params.threshlow:
                self.buy()

        if self.params.MACDtest and macd_value is not None and macd_signal is not None:
            if macd_value > macd_signal:
                self.buy()
            elif macd_value < macd_signal:
                self.sell()

        # Global stop-loss check
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.params.stoploss / 100)):
            self.close()

def runStrategy(params):
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(1000)

    data = yf.download("SPY")
    bt_data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(bt_data)
    
    cerebro.addstrategy(momentum,
                        RSItest=bool(params[0]),
                        MACDtest=bool(params[1]),
                        stoploss=float(params[2]),
                        threshigh=int(params[3]),
                        threshlow=int(params[4]),
                        short_period=int(params[5]),
                        long_period=int(params[6]),
                        positionsize=int(params[7]))
    
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



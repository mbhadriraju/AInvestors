import backtrader as bt
import yfinance as yf

class Contrarian(bt.Strategy):
    params = (
        ('deviation', float(input("Enter the Standard Deviation Factor: "))),
        ('fast_period', int(input("Enter the fast moving average period (Enter 1 for current price): "))),
        ('slow_period', int(input("Enter the slow moving average period: "))),
        ('stop_loss', int(input("Enter the stop loss: "))),
        ('position_size', int(input("Enter the position size: "))),
        ('rsi_period', int(input("Enter the RSI period: "))),
        ('rsi_oversold', int(input("Enter the RSI oversold threshold: "))),
        ('rsi_overbought', int(input("Enter the RSI overbought threshold: ")))
    )
    
    def __init__(self):
        # Mean Reversion Indicators
        self.dataclose = self.datas[0].close
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.p.slow_period)
        self.boll_bands = bt.indicators.BBands(self.dataclose, period=self.p.slow_period, devfactor=self.p.deviation, movav=self.slow_ma)
        
        # Contrarian RSI Indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(self.dataclose, period=self.p.rsi_period)
    
    def next(self):
        # Mean Reversion Logic (Bollinger Bands)
        if self.fast_ma < self.boll_bands.bot[-1]:  # Buy signal when below lower Bollinger Band
            if self.position.size < self.p.position_size:
                self.buy()
        elif self.fast_ma > self.boll_bands.top[-1]:  # Sell signal when above upper Bollinger Band
            if self.position.size * -1 < self.p.position_size:    
                self.sell()

        # Contrarian Logic (RSI)
        if self.rsi < self.p.rsi_oversold:  # Buy signal when RSI indicates oversold
            if self.position.size < self.p.position_size:
                self.buy()
        elif self.rsi > self.p.rsi_overbought:  # Sell signal when RSI indicates overbought
            if self.position.size * -1 < self.p.position_size:
                self.sell()

        # Stop-loss mechanism
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.p.stop_loss / 100)):
            self.close()

            
def runStrategy():
    cerebro = bt.Cerebro()
    
    cerebro.broker.set_cash(1000)
    
    # Download data for SPY
    data = yf.download("SPY")
    bt_data = bt.feeds.PandasData(dataname=data)
    
    cerebro.adddata(bt_data)
    
    # Add strategy to cerebro
    cerebro.addstrategy(Contrarian)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='myret')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='mysqn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydd')
    
    # Run the strategy
    strat = cerebro.run()[0]
    
    # Print results
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


# Run the strategy
runStrategy()

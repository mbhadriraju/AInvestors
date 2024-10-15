import backtrader as bt
import yfinance as yf

class Contrarian(bt.Strategy):
    def __init__(self, params):
        self.deviation = params[0]
        self.fast_period = params[1]
        self.slow_period = params[2]
        self.stop_loss = params[3]
        self.position_size = params[4]
        self.rsi_period = params[5]
        self.rsi_oversold = params[6]
        self.rsi_overbought = params[7]
        # Mean Reversion Indicators
        self.dataclose = self.datas[0].close
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.slow_period)
        self.boll_bands = bt.indicators.BBands(self.dataclose, period=self.slow_period, devfactor=self.deviation, movav=self.slow_ma)
        
        # Contrarian RSI Indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(self.dataclose, period=self.rsi_period)
    
    def next(self):
        # Mean Reversion Logic (Bollinger Bands)
        if self.fast_ma < self.boll_bands.bot[-1]:  # Buy signal when below lower Bollinger Band
            if self.position.size < self.position_size:
                self.buy()
        elif self.fast_ma > self.boll_bands.top[-1]:  # Sell signal when above upper Bollinger Band
            if self.position.size * -1 < self.position_size:    
                self.sell()

        # Contrarian Logic (RSI)
        if self.rsi < self.rsi_oversold:  # Buy signal when RSI indicates oversold
            if self.position.size < self.position_size:
                self.buy()
        elif self.rsi > self.rsi_overbought:  # Sell signal when RSI indicates overbought
            if self.position.size * -1 < self.position_size:
                self.sell()

        # Stop-loss mechanism
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.stop_loss / 100)):
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

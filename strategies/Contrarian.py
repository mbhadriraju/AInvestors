import backtrader as bt
import yfinance as yf

class Contrarian(bt.Strategy):
    params = (
        ('deviation', 2),
        ('fast_period', 10),
        ('slow_period', 30),
        ('stop_loss', 5),
        ('position_size', 100),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
    )

    def __init__(self):
        # Mean Reversion Indicators
        self.dataclose = self.datas[0].close
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.params.slow_period)
        self.boll_bands = bt.indicators.BBands(self.dataclose, period=self.params.slow_period, 
                                               devfactor=self.params.deviation, movav=self.slow_ma)
        
        # Contrarian RSI Indicator
        self.rsi = bt.indicators.RelativeStrengthIndex(self.dataclose, period=self.params.rsi_period)
    
    def next(self):
        # Mean Reversion Logic (Bollinger Bands)
        if self.fast_ma < self.boll_bands.bot[-1]:  # Buy signal when below lower Bollinger Band
            if self.position.size < self.params.position_size:
                self.buy()
        elif self.fast_ma > self.boll_bands.top[-1]:  # Sell signal when above upper Bollinger Band
            if self.position.size * -1 < self.params.position_size:    
                self.sell()

        # Contrarian Logic (RSI)
        if self.rsi < self.params.rsi_oversold:  # Buy signal when RSI indicates oversold
            if self.position.size < self.params.position_size:
                self.buy()
        elif self.rsi > self.params.rsi_overbought:  # Sell signal when RSI indicates overbought
            if self.position.size * -1 < self.params.position_size:
                self.sell()

        # Stop-loss mechanism
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.params.stop_loss / 100)):
            self.close()

def runStrategy(params):
    cerebro = bt.Cerebro()
    
    cerebro.broker.set_cash(1000)
    
    # Download data for SPY
    data = yf.download("SPY")
    bt_data = bt.feeds.PandasData(dataname=data)
    
    cerebro.adddata(bt_data)
    
    # Add strategy to cerebro
    cerebro.addstrategy(Contrarian,
                        deviation=float(params[0]),
                        fast_period=float(params[1]),
                        slow_period=float(params[2]),
                        stop_loss=float(params[3]),
                        position_size=float(params[4]),
                        rsi_period=float(params[5]),
                        rsi_oversold=float(params[6]),
                        rsi_overbought=float(params[7]))
    
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

# Example usage

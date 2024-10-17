import backtrader as bt
import yfinance as yf

class breakout(bt.Strategy):
    def __init__(self, params):
        self.deviation = params[0]
        self.fast_period = params[1]
        self.slow_period = params[2]
        self.stop_loss = params[3]
        self.position_size = params[4]
        self.dataclose = self.datas[0].close
        self.fast_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(self.dataclose, period=self.slow_period)
        self.boll_bands = bt.indicators.BBands(self.dataclose, period=self.slow_period, devfactor=self.deviation, movav=self.slow_ma)
    def next(self):
        if self.fast_ma > self.boll_bands.top[-1]:
            if self.position.size < self.position_size:
                self.buy()
        elif self.fast_ma < self.boll_bands.bot[-1]:
            if self.position.size * -1 < self.position_size:    
                self.sell()
        if self.broker.getvalue() < self.broker.get_cash() * (1 - (self.stop_loss / 100)):
            self.close()

            
def runStrategy(params):
    cerebro = bt.Cerebro()
    

    cerebro.broker.set_cash(1000)
    data = yf.download("SPY")
    bt_data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(bt_data)
    cerebro.addstrategy(breakout(params))
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
     

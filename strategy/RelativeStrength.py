import yfinance as yf
import backtrader as bt
import numpy as np

class RelativeStrength(bt.Strategy):
    def __init__(self, params):
        self.lookback = float(params[0])
        self.numberHold = float(params[1])
        self.stopLoss = float(params[2])
        self.assets = params[3].split(",")
        self.long_only = bool(params[4])
        # Store the asset tickers
        self.assets = [asset.strip() for asset in self.assets]
        
        # Download data for each asset and store the close prices
        self.datacloses = [
            np.log1p(yf.download(ticker)["Close"][self.lookback * -21:].pct_change().dropna()).to_numpy()
            for ticker in self.assets
        ]

    def next(self):
        # Risk-free rate (simplified to last available value of the 13-week T-bill)
        rfrate = yf.download("^IRX", period='1d')["Adj Close"].iloc[-1] / 100
        
        # Calculate average returns and standard deviations for Sharpe ratios
        avg_returns = [np.mean(self.datacloses[i]) for i in range(len(self.datacloses))]
        volatilities = [np.std(self.datacloses[j]) for j in range(len(self.datacloses))]
        sharpes = [(avg_returns[k] - rfrate) / volatilities[k] if volatilities[k] != 0 else 0 
                   for k in range(len(self.datacloses))]
        
        # Create a dictionary of assets and their Sharpe ratios
        sharpe_dict = {self.assets[l]: sharpes[l] for l in range(len(self.datacloses))}
        
        # Sort assets by Sharpe ratio in descending order
        sorted_assets = sorted(sharpe_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Get the top assets based on the numberHold parameter
        top_assets = [asset[0] for asset in sorted_assets[:self.numberHold]]
        
        # Trading logic
        for asset in self.assets:
            if asset in top_assets:
                # If not already in position, enter the market
                if not self.getpositionbyname(asset).size:
                    if self.long_only:
                        self.buy(data=self.getdatabyname(asset))
                    else:
                        self.buy(data=self.getdatabyname(asset)) if sharpe_dict[asset] > 0 else self.sell(data=self.getdatabyname(asset))
            else:
                # If in position but not a top asset, close the position
                if self.getpositionbyname(asset).size:
                    self.close(data=self.getdatabyname(asset))

        # Global stop-loss check
        if self.broker.getvalue() < self.broker.get_cash() * (1 - self.stopLoss / 100):
            self.close()
            print('Stop loss triggered, closing all positions.')


def runStrategy(params):
    cerebro = bt.Cerebro()
    

    cerebro.broker.set_cash(1000)
    strategy = RelativeStrength(params)
    for ticker in strategy.params.assets:
        data = bt.feeds.PandasData(dataname=yf.download(ticker, period=f'{strategy.params.lookback}d'))
        cerebro.adddata(data, name=ticker)
    cerebro.addstrategy(strategy)
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
            

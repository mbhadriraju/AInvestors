from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)

# Example strategy model
class Strategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Strategy {self.name}>'

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        strat = request.form.get("strategy")
        if strat:
            import main  # Ensure this module exists and is correctly implemented
            strat_type = main.generate_strat(strat)
            if strat_type == ["Arbitrage"]:
                params = [
                    "Spread Threshold: ",
                    "Max position size: "
                ]
            elif strat_type == ["Breakout"]:
                params = [
                    "Enter the Standard Deviation Factor: ",
                    "Enter the fast moving average period (Enter 1 for current price): ",
                    "Enter the slow moving average period: ",
                    "Enter the stop loss: ",
                    "Enter the position size: "
                ]
            elif strat_type == ["Contrarian"]:
                params = [
                    "Enter the Standard Deviation Factor: ",
                    "Enter the fast moving average period (Enter 1 for current price): ",
                    "Enter the slow moving average period: ",
                    "Enter the stop loss: ",
                    "Enter the position size: ",
                    "Enter the RSI period: ",
                    "Enter the RSI oversold threshold: ",
                    "Enter the RSI overbought threshold: "
                ]
            elif strat_type == ["Mean Reversion"]:
                params = [
                    "Enter the Standard Deviation Factor: ",
                    "Enter the fast moving average period (Enter 1 for current price): ",
                    "Enter the slow moving average period: ",
                    "Enter the stop loss: ",
                    "Enter the position size: "
                ]
            elif strat_type == ["Momentum"]:
                params = [
                    "Enter 'True' or 'False' to add the RSI indicator: ",
                    "Enter 'True' or 'False' to add the MACD indicator: ",
                    "Enter the stop loss: ",
                    "Enter the upper threshold: ",
                    "Enter the lower threshold: ",
                    "Enter the short moving average period: ",
                    "Enter the long moving average period: ",
                    "Max position size: "
                ]
            elif strat_type == ["Moving Average"]:
                params = [
                    "Enter the number of months to calculate the long moving average: ",
                    "Enter the moving average type (sma, ema, dema, tema): ",
                    "Enter the max position size: ",
                    "Enter the stop loss: "
                ]
            elif strat_type == ["Pairs"]:
                params = [
                    "Enter the Standard Deviation Factor: ",
                    "Enter the fast moving average period (Enter 1 for current price): ",
                    "Enter the slow moving average period: ",
                    "Enter the stop loss: ",
                    "Enter the position size: "
                ]
            if strat_type == ["Relative Strength"]:
                params = [
                    "Enter the lookback period (months): ",
                    "Number of assets to hold (If long+short, your input will be doubled): ",
                    "Enter the stop loss percentage: ",
                    "Enter the ticker symbols of the assets (comma-separated): ",
                    "Long Only? (True or False): "
                ]
            else:
                params = [
                    "Max position size: ", 
                    "Period: "
                    ]
            
            params = [request.form.get(param) for param in params]
            strat_results = main.generate_strat_code(strat_type, params)
            return render_template("index.html", strat=strat, metrics=strat_results)
        else:
            return render_template("index.html", error="Strategy is required.")
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

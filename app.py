from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Example strategy model
class Strategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Strategy {self.name}>'

@app.route("/", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "strategy" in request.form:
            strat = request.form.get("strategy")
            if strat:
                data = pd.read_csv("database/StratDescriptions.csv")
                # Initialize TF-IDF Vectorizer
                vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)
                # Transform the text data to feature vectors
                X = vectorizer.fit_transform(data['Description'])
                # Labels
                y = data["Type"]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=101)
                rfmod = RandomForestClassifier(oob_score=True)
                rfmod.fit(X_train, y_train)
                print(rfmod.oob_score_)
                print(f'Train Accuracy - : {rfmod.score(X_train,y_train)}')
                print(f'Test Accuracy - : {rfmod.score(X_test,y_test)}')  
                # Preprocess the user input using the trained vectorizer
                user_input_transformed = vectorizer.transform([strat]) 
                strat_type = rfmod.predict(user_input_transformed) 
                print(strat_type)
                params = get_params_for_strategy(strat_type)
                return render_template("index.html", strat=strat, strat_type=strat_type, params=params)
            else:
                return render_template("index.html", error="Strategy is required.")
        if "param_submit" in request.form:
            strat = request.form.get("strat")
            strat_type = request.form.get("strat_type")
            params = [value for key, value in request.form.items()
                      if key not in ["param_submit", "strat", "strat_type"]]
            if strat_type == "['Contrarian']":
                from strategies import Contrarian as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Pairs']":
                from strategies import Pairs as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Arbitrage']":
                from strategies import Arbitrage as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Relative Strength']":
                from strategies import RelativeStrength as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Breakout']":
                from strategies import Breakout as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Volume Based']":
                from strategies import Volume as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Mean Reversion']":
                from strategies import MeanReversion as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Momentum']":
                from strategies import Momentum as strategy
                strat_results = strategy.runStrategy(params)

            if strat_type == "['Moving Average']":
                from strategies import MovingAverage as strategy
                strat_results = strategy.runStrategy(params)
            return render_template("index.html", strat=strat, metrics=strat_results)
    return render_template("index.html")

def get_params_for_strategy(strat_type):
    params_dict = {
        "Arbitrage": [
            "Spread Threshold",
            "Max position size"
        ],
        "Breakout": [
            "Enter the Standard Deviation Factor",
            "Enter the fast moving average period (Enter 1 for current price)",
            "Enter the slow moving average period",
            "Enter the stop loss",
            "Enter the position size"
        ],
        "Contrarian": [
            "Enter the Standard Deviation Factor",
            "Enter the fast moving average period (Enter 1 for current price)",
            "Enter the slow moving average period",
            "Enter the stop loss",
            "Enter the position size",
            "Enter the RSI period",
            "Enter the RSI oversold threshold",
            "Enter the RSI overbought threshold"
        ],
        "Mean Reversion": [
            "Enter the Standard Deviation Factor",
            "Enter the fast moving average period (Enter 1 for current price)",
            "Enter the slow moving average period",
            "Enter the stop loss",
            "Enter the position size"
        ],
        "Momentum": [
            "Enter 'True' or 'False' to add the RSI indicator",
            "Enter 'True' or 'False' to add the MACD indicator",
            "Enter the stop loss",
            "Enter the upper threshold",
            "Enter the lower threshold",
            "Enter the short moving average period",
            "Enter the long moving average period",
            "Max position size"
        ],
        "Moving Average": [
            "Enter the number of months to calculate the long moving average",
            "Enter the moving average type (sma, ema, dema, tema)",
            "Enter the max position size",
            "Enter the stop loss"
        ],
        "Pairs": [
            "Enter the Standard Deviation Factor",
            "Enter the fast moving average period (Enter 1 for current price)",
            "Enter the slow moving average period",
            "Enter the stop loss",
            "Enter the position size"
        ],
        "Relative Strength": [
            "Enter the lookback period (months)",
            "Number of assets to hold (If long+short, your input will be doubled)",
            "Enter the stop loss percentage",
            "Enter the ticker symbols of the assets (comma-separated)",
            "Long Only? (True or False)"
        ]
    }
    return params_dict.get(strat_type[0])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

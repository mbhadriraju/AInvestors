from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os
from groq import Groq

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database + Strategy for future addons to improve user experience.
with app.app_context():
    db.create_all()

class Strategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Strategy {self.name}>'

@app.route("/model", methods=["GET", "POST"])
def model():
    if request.method == "POST":
        if "strategy" in request.form:
            strat = request.form.get("strategy")
            if strat:
                client = Groq(
                    api_key=os.environ.get("GROQ_ENV_KEY"),
                )
                conversation_id = None
                conversation_history = [
                    {
                        "role": "system",
                        "content": "The user will input their trading strategy and then you create a program in python that uses libraries like Backtrader and YFinance that essentially creates a class for the strategy and then a function called 'main' that backtests the strategy on major stock indices over various periods. The main method will finally output a string with strategy results. When you return the code, only return the code, not any of your own comments as well that explain what the code does. The metrics you should output are Annual Return, Sharpe Ratio, and Drawdown. Note that when you have the yfinance data, columns attribute of the DataFrame is a MultiIndex, which is a hierarchical index. Make sure not to call The lower() method which can cause an error. To fix this, you can try resetting the column index to a single-level index using the columns attribute or selecting only the columns that you need. Also, do not plot anything. Also, ensure the main function does not require any parameters, they should already have been defined by the user."
                    },
                    {
                        "role": "user",
                        "content": strat,
                    }
                ]

                while True:
                    try:
                        chat_completion = client.chat.completions.create(
                            conversation_id=conversation_id,
                            messages=conversation_history,
                            model="llama-3.1-70b-versatile",
                        )
                        conversation_id = chat_completion.conversation_id
                        code_results = chat_completion.choices[0].message.content
                        code_results = code_results.replace("```python\n", "")
                        code_results = code_results.replace("```", "")
                        with open("strategy/new.py", "w") as new_file:
                            new_file.write(code_results)
                        from strategy.new import main as strat_main
                        strat_results = strat_main()
                        break
                    except Exception as e:
                        error_message = f"An error occurred: {str(e)}"
                        conversation_history.append(
                            {
                                "role": "assistant",
                                "content": error_message,
                            }
                        )
                        conversation_history.append(
                            {
                                "role": "user",
                                "content": "Please revise the code to fix the error.",
                            }
                        )
                return render_template("model.html", strat=strat, metrics=strat_results)
    return render_template("model.html")

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/pricing", methods=["GET", "POST"])
def pricing():
    return render_template("pricing.html")

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
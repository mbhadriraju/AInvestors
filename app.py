from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os
from groq import Groq
import openai

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
key = "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"
"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"
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
                client = openai.OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key="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"
                )
                system_message = f"""
                    Create a Python program using Backtrader and yfinance to implement and backtest a trading strategy. Follow these guidelines:
                    1. Create a Strategy class inheriting from bt.Strategy.
                    2. Implement a 'main' function that sets up and runs the backtest, returning a string with the results.
                    3. Use major stock indices for testing over various periods unless the user specifies something different. (ex. SPY, DJIA, ^IXIC). The user can specify something different.
                    4. Output metrics should include Annual Return and Sharpe Ratio or other metrics as specified by the user. Please compute them manually as the backtrader API can make errors.
                    5. IMPORTANT: When using the yfinance API, do NOT use bt.feeds.PandasData as that method has an error, instead use bt.feeds.PandasDirectData
                    6. Do not plot anything.
                    7. Ensure the main function doesn't require parameters since they should be defined within the function.
                    8. Do not use a shutdown() method on Cerebro objects. Just use run().
                    9. Return only the Python code, without any explanatory comments. For example, do not say 'here is the revised code' or 'this code does...'. NO text should be present other than the code itself.
                    10. If the user enters nonsense, just have the main method return a string that says that the user must enter a valid strategy.
                    11. If you make an error in the code, try again and note what the error was.
                    12. IMPORTANT: The 'DataFrame' object has no attribute 'setenvironment' therefore, that method does NOT work!
                    13. There should be no input functions, this should all be done automatically, if the user does not specify further than their strategy, just add a few indices and some relevent start+end dates, don't make any input functions.
                    14. The current date is {datetime.now()}
                    15. The output should look like each index followed by the metrics for that index. (unless the user specifies something else).
                    """
                conversation_history = [
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": strat,
                    }
                ]
                while True:
                    try:
                        chat_completion = client.chat.completions.create(
                            messages=conversation_history,
                            model="gpt-4o",
                            temperature=.4,
                            top_p=.2,
                            frequency_penalty=.3,
                            presence_penalty=.15
                        )
                        code_results = chat_completion.choices[0].message.content
                        code_results = code_results.replace("```python\n", "")
                        code_results = code_results.replace("```", "")
                        print(code_results)
                        with open("strategy/new.py", "w") as new_file:
                            new_file.write(code_results)
                        from strategy.new import main as strat_main
                        strat_results = strat_main()
                        break
                    except Exception as e:
                        error_message = f"An error occurred: {str(e)}"
                        print(error_message)
                        conversation_history[1] = {
                                "role": "user",
                                "content": "You made this error: " + error_message + "Please revise this code to fix the error: " + open("strategy/new.py", "r").read(),
                            }

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
    app.run(debug=True, use_reloader=False)

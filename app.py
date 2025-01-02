from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import os
from groq import Groq
import openai
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#Insert Key
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(125), nullable=False)
   
    def set_password(self, password):
       self.password = generate_password_hash(password)
   
    def check_password(self, password):
       return check_password_hash(self.password, password)
    
    date_joined = db.Column(db.Date, default=datetime.utcnow)



@app.route("/model", methods=["GET"])
def model_page():
    if "username" not in session:  
        return render_template("model.html", login=False)
    return render_template("model.html", login=True)

@app.route("/model", methods=["POST"])
def model():
    if "username" not in session:  
        return render_template("model.html", login=False)
    if request.method == "POST":
        if "strategy" in request.form:
            strat = request.form.get("strategy")
            if strat:
                client = openai.OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    #Insert Key
                )
                system_message = f"""
                    Create a Python program using Backtrader and yfinance to implement and backtest a trading strategy. Follow these guidelines:
                    1. Create a Strategy class inheriting from bt.Strategy.
                    2. Implement a 'main' function that sets up and runs the backtest, returning a string with the results.
                    3. Use major stock indices for testing over various periods unless the user specifies something different. use ^GSPC, ^DJI, ^IXIC unless the user specifies something else. The user can specify something different.
                    4. Output metrics should include Annual Return and Sharpe Ratio or other metrics as specified by the user. Use the backtrader api to get the metrics unless the user specifies a metric that backtrader doesn't have. In that case, calculate it on your own.
                    5. IMPORTANT: When using the yfinance API, make sure to use this method to remove the ticker from the data since the keys for each column are tuples, use these methods: df = yf.download(ticker) and then df.columns = df.columns.droplevel(1) to remove the ticker symbol from the yfinance data so that the PandasData method doesn't have to convert a tuple to lowercase. DO NOT USE df.columns.droplevel(0), you need to use df.columns.droplevel(1)
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
                    16. Remember the yfinance data is daily data.
                    17. Here is a list of the metrics provided by backtrader API, others will need to be calculated manually: AnnualReturn, Calmar, DrawDown, TimeDrawDown, GrossLeverage, PositionsValue, PyFolio, LogReturnsRolling, PeriodStats, Returns, SharpeRatio, SharpeRatio_A, SQN, TimeReturn, TradeAnalyzer, Transactions, VWR. 
                    18. The backtrader API returns the metrics in an OrderedDict format, please account for this and fix it. For metrics like annual return, it will contain multiple elements for each year but for some like the sharpe ratio, it will only contain one. YOU NEED TO CONVERT IT INTO A FLOAT VALUE!!!
                    19. If you are going to change the size of the position that the user will go into, make sure you account for the balance in the account, otherwise, there may not be enough funds to actually make a trade. 
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
                with open("strategy/new.py", "w") as new_file:
                    new_file.write("")
                return render_template("model.html", login=True, strat=strat, metrics=strat_results)



@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route("/pricing", methods=["GET", "POST"])
def pricing():
    return render_template("pricing.html")

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET"])
def login_page():
    if "username" not in session:
        return render_template("login.html")
    else:
        return render_template("login.html", login=True)

@app.route("/signup", methods=["GET"])
def signup_page():
    if "username" not in session:
        return render_template("signup.html")
    else:
        return render_template("login.html", login=True)

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["Name"]
    email = request.form["Email"]
    password = request.form["Password"]

    if not (email and name and password):
        return render_template("signup.html", error="Please enter both email and password.")
    
    user = User.query.filter_by(email=email).first()

    if user:
        return render_template("signup.html", error="Account already present! Please login using the login page.")
    else:
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session["username"] = new_user.name
        return redirect(url_for("home"))

@app.route("/login", methods=["POST"])
def login():
    email = request.form["Email"]
    password = request.form["Password"]

    if not email or not password:
        return render_template("login.html", error="Please enter both email and password.")

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session["username"] = user.name  
        session["user_id"] = user.id     
        return redirect(url_for("home"))  
    else:
        return render_template("login.html", error="Invalid email or password.")
    

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)

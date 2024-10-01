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
            import hi  # Ensure this module exists and is correctly implemented
            generated_code = hi.generate_strat_code(strat)
            return render_template("index.html", strat=strat, generated_code=generated_code)
        else:
            return render_template("index.html", error="Strategy is required.")
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

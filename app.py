from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import BertTokenizer, BertModel, AdamW, get_linear_schedule_with_warmup

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
                #Method to load data and return descriptions with their appropriate labels.
                def loadData(csv):
                    df = pd.read_csv(csv)
                    descriptions = df["Description"].tolist()
                    arr = ["Arbitrage", "Breakout", "Contrarian", "Mean Reversion", "Momentum", "Moving Average", "Pairs", "Relative Strength", "Volume Based"]
                    labels = []
                    for label in df["Label"].tolist():
                        labels.append([1 if label == arr[i] else 0 for i in range(len(arr))])
                    return descriptions, labels
                #A TextClassificationDataset object with special attributes for ease of classification.
                class TextClassificationDataset(Dataset):
                    def __init__(self, descriptions, labels, tokenizer, max_length):
                        self.descriptions = descriptions
                        self.labels = labels
                        self.tokenizer = tokenizer
                        self.max_length = max_length
                    def __len__(self):
                        return len(self.descriptions)
                    def __getitem__(self, idx):
                        description = self.descriptions[idx]
                        label = self.labels[idx]
                        encoding = self.tokenizer(description, return_tensors='pt', max_length=self.max_length, padding='max_length', truncation=True)
                        return {'input_ids': encoding['input_ids'].flatten(), 'attention_mask': encoding['attention_mask'].flatten(), 'label': torch.tensor(label)}
                #An object that classifies using BERT
                class BERTClassifier(nn.Module):
                    def __init__(self, bert_model_name, num_classes):
                        super(BERTClassifier, self).__init__()
                        self.bert = BertModel.from_pretrained(bert_model_name)
                        self.dropout = nn.Dropout(0.1)
                        self.fc = nn.Linear(self.bert.config.hidden_size, num_classes)
                    def forward(self, input_ids, attention_mask):
                            outputs = self.bert(input_ids, attention_mask)
                            pooled_output = outputs.pooler_output
                            x = self.dropout(pooled_output)
                            logits = self.fc(x)
                            return logits
                #A function that trains the model and uses the optimizer to perform gradient descent. 
                def train(model, data_loader, optimizer, scheduler, device):
                    model.train()
                    for batch in data_loader:
                        optimizer.zero_grad()
                        input_ids = batch['input_ids'].to(device)
                        attention_mask = batch['attention_mask'].to(device)
                        labels = batch['label'].to(device)
                        outputs = model.forward(input_ids, attention_mask)
                        loss = nn.CrossEntropyLoss()(outputs, labels)
                        loss.backward()
                        optimizer.step()
                        scheduler.step()
                #A function that evaluates the model performance
                def evaluate(model, data_loader, device):
                    model.eval()
                    predictions = []
                    actual_labels = []
                    with torch.no_grad():
                        for batch in data_loader:
                            input_ids = batch['input_ids'].to(device)
                            attention_mask = batch['attention_mask'].to(device)
                            labels = batch['label'].to(device)
                            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                            _, preds = torch.max(outputs, dim=1)
                            predictions.extend(preds.cpu().tolist())
                            actual_labels.extend(labels.cpu().tolist())
                    return accuracy_score(actual_labels, predictions), classification_report(actual_labels, predictions)
                #The final function that predicts the strategy with the text and trained model.
                def predict_strat(text, model, tokenizer, device, max_length=128):
                    model.eval()
                    encoding = tokenizer(text, return_tensors='pt', max_length=max_length, padding='max_length', truncation=True)
                    input_ids = encoding['input_ids'].to(device)
                    attention_mask = encoding['attention_mask'].to(device)

                    with torch.no_grad():
                        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                        _, preds = torch.max(outputs, dim=1)
                    arr = ["Arbitrage", "Breakout", "Contrarian", "Mean Reversion", "Momentum", "Moving Average", "Pairs", "Relative Strength", "Volume Based"]
                    test = preds.item()
                    for i in range(len(test)):
                        if test[i] == 1:
                            return arr[i]
                bert_model_name = 'bert-base-uncased'
                num_classes = 2
                max_length = 128
                batch_size = 16
                num_epochs = 4
                learning_rate = 2e-5
                descriptions, labels = loadData("database/StratDescriptions.csv")
                train_descriptions, val_texts, train_labels, val_labels = train_test_split(descriptions, labels, test_size=0.2, random_state=42)
                tokenizer = BertTokenizer.from_pretrained(bert_model_name)
                train_dataset = TextClassificationDataset(train_descriptions, train_labels, tokenizer, max_length)
                val_dataset = TextClassificationDataset(val_texts, val_labels, tokenizer, max_length)
                train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
                val_dataloader = DataLoader(val_dataset, batch_size=batch_size)
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = BERTClassifier(bert_model_name, num_classes).to(device)
                optimizer = AdamW(model.parameters(), lr=learning_rate)
                total_steps = len(train_dataloader) * num_epochs
                scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)
                for epoch in range(num_epochs):
                    print(f"Epoch {epoch + 1}/{num_epochs}")
                    train(model, train_dataloader, optimizer, scheduler, device)
                    accuracy, report = evaluate(model, val_dataloader, device)
                    print(f"Validation Accuracy: {accuracy:.4f}")
                    print(report)
                torch.save(model.state_dict(), "bert_classifier.pth")
                strat_type = predict_strat(strat, model, tokenizer, device)
                '''
                data = pd.read_csv("database/StratDescriptions.csv")
                descriptions, types = loadData("database/StratDescriptions.csv")
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
                '''
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

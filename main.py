import spacy
import yfinance as yf
import numpy as np
import backtrader as bt
import sys
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
from sklearn.feature_extraction.text import TfidfVectorizer

#Generate the trading strategy code
def generate_strat_code(user_input):
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
    user_input_transformed = vectorizer.transform([user_input])
    
    # Predict the strategy type based on the user input
    predicted_strategy = rfmod.predict(user_input_transformed)  
    print(f"Predicted Strategy: {predicted_strategy}")  
    if predicted_strategy == ["Contrarian"]:
        from strategies import Contrarian as strat
        return strat.runStrategy()

    if predicted_strategy == ["Pairs"]:
        from strategies import Pairs as strat
        return strat.runStrategy()

    if predicted_strategy == ["Arbitrage"]:
        from strategies import Arbitrage as strat
        return strat.runStrategy()

    if predicted_strategy == ["Relative Strength"]:
        from strategies import RelativeStrength as strat
        return strat.runStrategy()

    if predicted_strategy == ["Breakout"]:
        from strategies import Breakout as strat
        return strat.runStrategy()

    if predicted_strategy == ["Volume Based"]:
        from strategies import Volume as strat
        return strat.runStrategy()

    if predicted_strategy == ["Mean Reversion"]:
        from strategies import MeanReversion as strat
        return strat.runStrategy()

    if predicted_strategy == ["Momentum"]:
        from strategies import Momentum as strat
        return strat.runStrategy()

    if predicted_strategy == ["Moving Average"]:
        from strategies import MovingAverage as strat
        return strat.runStrategy()
      

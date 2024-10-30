from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import BertTokenizer, BertModel, AdamW

def loadData(csv):
    df = pd.read_csv(csv)
    descriptions = df["Description"].tolist()
    arr = ["Arbitrage", "Breakout", "Contrarian", "Mean Reversion", "Momentum", "Moving Average", "Pairs", "Relative Strength", "Volume Based"]
    types = []
    for type in df["Type"].tolist():
        types.append([1 if type == arr[i] else 0 for i in range(len(arr))])
    return descriptions, types

print(loadData("database/StratDescriptions.csv"))
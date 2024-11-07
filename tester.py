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

df = pd.read_csv("database/StratDescriptions.csv")

print(df["Label"])
from transformers import DistilBertTokenizer
import pandas as pd, numpy as np

EPOCHS = 15

df = pd.read_csv(r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Jarvis\jarvis_intent_dataset.csv")

tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
tokenizer(df.text, padding=True, truncation=True, return_tensors='pt')
label2id = {"open" : 0, "search" : 1, "play" : 2, "stop" : 3, "chat" : 4}

df = df["intent"] = label2id["intent"].get()

X = []
y = []

for epoch in range(EPOCHS):
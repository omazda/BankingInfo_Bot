import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import warnings
warnings.filterwarnings('ignore')

data = pd.read_csv('data.csv')
X = data.drop(columns='satisfaction')
y = data['satisfaction']
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, random_state=1000)
model = LogisticRegression(penalty='none')
model.fit(X_train, y_train)
model.predict(X_train)
model.predict_proba(X_train)
model.score(X_train, y_train)
precision_score(y_train, model.predict(X_train))

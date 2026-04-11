
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

dados = {
    "temperatura": [40, 42, 45, 50, 55, 60, 65, 70, 80, 85, 90, 48, 52, 67, 73, 88],
    "vibracao":    [0.3, 0.4, 0.5, 0.7, 0.8, 0.9, 1.2, 1.3, 1.5, 1.7, 1.9, 0.6, 0.75, 1.1, 1.4, 1.8],
    "rpm":         [900, 950, 1000, 1100, 1150, 1200, 1300, 1400, 1500, 1600, 1700, 1050, 1120, 1280, 1450, 1650],
    "falha":       [0,   0,   0,    0,    0,    1,    1,    1,    1,    1,    1,    0,    0,    1,    1,    1]
}

df = pd.DataFrame(dados)
df.to_csv("exemplo_dados.csv", index=False)

X = df[["temperatura", "vibracao", "rpm"]]
y = df["falha"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

preds = modelo.predict(X_test)
print(classification_report(y_test, preds))

with open("modelo_falha_rf.pkl", "wb") as f:
    pickle.dump(modelo, f)

print("Modelo salvo como modelo_falha_rf.pkl")
print("Dataset salvo como exemplo_dados.csv")

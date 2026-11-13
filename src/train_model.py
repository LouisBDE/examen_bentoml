# src/train_model.py

import numpy as np
import pandas as pd
import bentoml
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

PROCESSED_DIR = "data/processed"
MODEL_NAME = "admission_lr"


def load_data():
    """Charge les 4 CSV préparés."""
    X_train = pd.read_csv(f"{PROCESSED_DIR}/X_train.csv")
    X_test = pd.read_csv(f"{PROCESSED_DIR}/X_test.csv")
    y_train = pd.read_csv(f"{PROCESSED_DIR}/y_train.csv").values.ravel()
    y_test = pd.read_csv(f"{PROCESSED_DIR}/y_test.csv").values.ravel()
    return X_train, X_test, y_train, y_test


def main():
    # 1. Charger les données
    X_train, X_test, y_train, y_test = load_data()

    # 2. Créer et entraîner le modèle
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 3. Évaluer sur le jeu de test
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    # scikit-learn 1.3.2 : pas de root_mean_squared_error, on passe par np.sqrt
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"R²   sur le jeu de test : {r2:.4f}")
    print(f"RMSE sur le jeu de test : {rmse:.4f}")

    # 4. Sauvegarder dans le Model Store de BentoML
    tag = bentoml.sklearn.save_model(MODEL_NAME, model)
    print(f"Modèle sauvegardé : {tag}")


if __name__ == "__main__":
    main()

# src/prepare_data.py

import os
import pandas as pd
from sklearn.model_selection import train_test_split

RAW_PATH = "data/raw/admission.csv"
PROCESSED_DIR = "data/processed"
TARGET_COL = "chance_of_admit"
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_data(path: str) -> pd.DataFrame:
    """Charge les données brutes."""
    return pd.read_csv(path)


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les noms de colonnes : trim + snake_case."""
    df = df.copy()
    df.columns = [
        col.strip().lower().replace(" ", "_").replace(".", "")
        for col in df.columns
    ]
    # "lor" (avec espace final dans le fichier brut) -> "lor"
    df = df.rename(columns={"lor": "lor"})
    return df


def drop_useless_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les colonnes inutiles pour la modélisation."""
    return df.drop(columns=["serial_no"])


def split_features_target(df: pd.DataFrame):
    """Sépare les features X de la cible y."""
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]
    return X, y


def main():
    # 1. Charger les données
    df = load_data(RAW_PATH)

    # 2. Nettoyer les noms de colonnes
    df = clean_columns(df)

    # 3. Supprimer la colonne inutile (Serial No.)
    df = drop_useless_columns(df)

    # 4. Séparer features et cible
    X, y = split_features_target(df)

    # 5. Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    # 6. Sauvegarder dans data/processed
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    X_train.to_csv(os.path.join(PROCESSED_DIR, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(PROCESSED_DIR, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(PROCESSED_DIR, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(PROCESSED_DIR, "y_test.csv"), index=False)

    print(f"Données préparées : X_train {X_train.shape}, X_test {X_test.shape}")


if __name__ == "__main__":
    main()

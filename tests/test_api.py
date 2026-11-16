# tests/test_api.py

import requests
import jwt


# --- Login ---

def test_login_identifiants_valides_renvoie_200_et_jwt_valide(base_url, timeout, jwt_secret):
    r = requests.post(
        f"{base_url}/login",
        json={"username": "admin", "password": "password"},
        timeout=timeout,
    )
    assert r.status_code == 200
    body = r.json()

    # Décoder le token prouve que c'est un vrai JWT signé par le service,
    # pas n'importe quelle chaîne présente sous la clé access_token.
    payload = jwt.decode(body["access_token"], jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == "admin"
    assert "exp" in payload


def test_login_mauvais_identifiants_renvoie_401(base_url, timeout):
    r = requests.post(
        f"{base_url}/login",
        json={"username": "admin", "password": "wrong"},
        timeout=timeout,
    )
    assert r.status_code == 401


# --- Sécurité de /predict ---

def test_predict_sans_token_renvoie_401(base_url, timeout, valid_input):
    r = requests.post(f"{base_url}/predict", json=valid_input, timeout=timeout)
    assert r.status_code == 401


def test_predict_token_mauvaise_signature_renvoie_401(base_url, timeout, valid_input, wrong_key_token):
    headers = {"Authorization": f"Bearer {wrong_key_token}"}
    r = requests.post(
        f"{base_url}/predict", json=valid_input, headers=headers, timeout=timeout
    )
    assert r.status_code == 401
    assert "invalide" in r.json()["error"]


def test_predict_token_expire_renvoie_401_et_message(base_url, timeout, valid_input, expired_token):
    headers = {"Authorization": f"Bearer {expired_token}"}
    r = requests.post(
        f"{base_url}/predict", json=valid_input, headers=headers, timeout=timeout
    )
    assert r.status_code == 401
    # Le message permet de distinguer "expiré" d'"invalide"
    assert "expiré" in r.json()["error"]


# --- Prédiction ---

def test_predict_token_valide_renvoie_200_et_prediction_plausible(base_url, timeout, auth_headers, valid_input):
    r = requests.post(
        f"{base_url}/predict", json=valid_input, headers=auth_headers, timeout=timeout
    )
    assert r.status_code == 200
    body = r.json()
    assert "prediction" in body
    # Une régression linéaire n'est pas bornée : elle peut sortir de [0, 1]
    # pour des profils extrêmes. On borne à [-0.5, 1.5] pour détecter les
    # aberrations (mauvaise colonne, mauvais ordre) sans faux positif.
    assert -0.5 <= body["prediction"] <= 1.5


def test_predict_donnees_invalides_renvoie_4xx(base_url, timeout, auth_headers):
    # cgpa de type string : rejeté par le schéma pydantic
    body = {"input_data": {
        "gre_score": 320, "toefl_score": 110, "university_rating": 3,
        "sop": 3.5, "lor": 3.5, "cgpa": "abc", "research": 1,
    }}
    r = requests.post(
        f"{base_url}/predict", json=body, headers=auth_headers, timeout=timeout
    )
    # Intervalle 4xx : robuste même si BentoML renvoie 422 au lieu de 400
    assert 400 <= r.status_code < 500


def test_predict_champ_manquant_renvoie_4xx(base_url, timeout, auth_headers):
    # research absent du corps
    body = {"input_data": {
        "gre_score": 320, "toefl_score": 110, "university_rating": 3,
        "sop": 3.5, "lor": 3.5, "cgpa": 8.6,
    }}
    r = requests.post(
        f"{base_url}/predict", json=body, headers=auth_headers, timeout=timeout
    )
    assert 400 <= r.status_code < 500

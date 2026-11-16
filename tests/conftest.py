# tests/conftest.py

import pytest
import requests
import jwt
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:3000"

# Mêmes valeurs que dans src/service.py (copiées, pas importées :
# les tests parlent à l'API par HTTP uniquement, comme un client externe)
API_USERNAME = "admin"
API_PASSWORD = "password"
JWT_SECRET = "change-me-secret-key"
JWT_ALGORITHM = "HS256"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def timeout():
    """Timeout HTTP pour tous les appels : un service muet fait
    échouer le test au lieu de le bloquer indéfiniment."""
    return 5


@pytest.fixture
def jwt_secret():
    """Clé secrète du service, pour décoder/forger des JWT dans les tests."""
    return JWT_SECRET


@pytest.fixture
def valid_token(base_url, timeout):
    """Se connecte et renvoie un JWT valide."""
    r = requests.post(
        f"{base_url}/login",
        json={"username": API_USERNAME, "password": API_PASSWORD},
        timeout=timeout,
    )
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(valid_token):
    """Headers d'authentification prêts à l'emploi pour /predict."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def valid_input():
    """Corps JSON valide pour /predict, enveloppé sous la clé input_data."""
    return {
        "input_data": {
            "gre_score": 320,
            "toefl_score": 110,
            "university_rating": 3,
            "sop": 3.5,
            "lor": 3.5,
            "cgpa": 8.6,
            "research": 1,
        }
    }


@pytest.fixture
def expired_token():
    """JWT signé avec la même clé que le service, mais déjà expiré."""
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    return jwt.encode(
        {"sub": "admin", "exp": past}, JWT_SECRET, algorithm=JWT_ALGORITHM
    )


@pytest.fixture
def wrong_key_token():
    """JWT valide en apparence, mais signé avec une autre clé :
    vérifie que le service contrôle la signature, pas seulement le format."""
    return jwt.encode(
        {"sub": "admin"}, "autre-cle-secrete", algorithm=JWT_ALGORITHM
    )

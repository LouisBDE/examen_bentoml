# src/service.py

from datetime import datetime, timedelta, timezone

import bentoml
import jwt
import pandas as pd
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# --- Configuration de l'authentification ---
API_USERNAME = "admin"
API_PASSWORD = "password"
JWT_SECRET = "change-me-secret-key"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_MINUTES = 60

# --- Colonnes attendues par le modèle (même ordre que X_train) ---
FEATURES = [
    "gre_score",
    "toefl_score",
    "university_rating",
    "sop",
    "lor",
    "cgpa",
    "research",
]


# --- Schéma pydantic d'entrée pour /predict ---
class StudentFeatures(BaseModel):
    gre_score: int
    toefl_score: int
    university_rating: int
    sop: float
    lor: float
    cgpa: float
    research: int


# --- Middleware JWT : protège tout sauf les routes autorisées ---
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Routes libres : login, Swagger UI (/), OpenAPI (/docs.json), santé
        if (
            path.startswith("/login")
            or path in ("/", "/docs.json", "/docs", "/readyz", "/healthz", "/health")
        ):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Token manquant. Connectez-vous via /login."},
            )
        token = auth.removeprefix("Bearer ")
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401, content={"error": "Token expiré."}
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401, content={"error": "Token invalide."}
            )
        return await call_next(request)


# --- Service BentoML 1.4 : classe décorée ---
# Le nom du service donne le tag du Bento : admission_prediction_service:latest
@bentoml.service(name="admission_prediction_service")
class AdmissionService:

    def __init__(self):
        # Chargé une seule fois, au démarrage du service
        self.model = bentoml.models.get("admission_lr:latest").load_model()

    @bentoml.api
    def login(self, username: str, password: str):
        """Endpoint de connexion : renvoie un JWT signé avec sub et exp.
        Mauvais identifiants -> réponse HTTP 401."""
        if username != API_USERNAME or password != API_PASSWORD:
            return JSONResponse(
                status_code=401,
                content={"error": "Identifiants invalides."},
            )

        now = datetime.now(timezone.utc)
        payload = {
            "sub": username,
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {"status": "ok", "access_token": token, "token_type": "bearer"}

    @bentoml.api
    def predict(self, input_data: StudentFeatures) -> dict:
        """Endpoint de prédiction : chance d'admission d'un étudiant."""
        features = pd.DataFrame([input_data.model_dump()])[FEATURES]
        prediction = self.model.predict(features)[0]
        return {"prediction": float(prediction)}

    @bentoml.api
    def health(self) -> dict:
        """Endpoint bonus : état du service."""
        return {"status": "ok", "model": "admission_lr:latest"}


# --- Attachement du middleware au service ---
AdmissionService.add_asgi_middleware(JWTAuthMiddleware)

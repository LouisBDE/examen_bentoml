# Admission Prediction Service

API de prédiction de la chance d'admission d'un étudiant en université
(modèle de régression linéaire, servi avec BentoML, sécurisé par JWT).

## 1. Prérequis

- Docker ;
- Python 3.12 (version utilisée pour l'entraînement et les tests) ;
- sous Ubuntu : le paquet `python3-venv`, sans lequel la création du venv échoue :

```bash
sudo apt install python3.12-venv
```

## 2. Extraire le projet

L'archive contient les fichiers à sa racine (sans dossier parent) : on l'extrait donc dans un dossier dédié.

```bash
mkdir rendu_bentoml
tar -xzf rendu_bentoml.tar.gz -C rendu_bentoml
cd rendu_bentoml
```

Toutes les commandes suivantes se lancent depuis ce dossier (celui qui contient `tests/`).

## 3. Charger l'image Docker

```bash
docker load -i admission_prediction_service.tar
```

## 4. Lancer le service

```bash
docker run -d --name admission_api -p 3000:3000 admission_prediction_service:latest
```

Le service tourne en arrière-plan et répond sur <http://localhost:3000>.
Vérifier qu'il est prêt (à relancer tant que la commande échoue) :

```bash
curl -X POST http://localhost:3000/health -H "Content-Type: application/json" -d '{}'
```

→ doit afficher `{"status": "ok", ...}`. En cas de problème : `docker logs admission_api`.

## 5. Préparer l'environnement de test

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 6. Lancer les tests

Le service doit tourner (étape 4). Venv activé :

```bash
pytest tests/ -v
```

Les 8 tests vérifient :

- le login : JWT valide, 401 sur mauvais identifiants ;
- la sécurité de `/predict` : 401 sans token, token expiré, mauvaise signature ;
- la prédiction : 200 avec une valeur plausible, rejet des données invalides.

## 7. Arrêter le service

```bash
docker stop admission_api && docker rm admission_api
```

Avant de relancer l'étape 4, exécuter cette étape, sinon `docker run` échoue avec « name already in use ».

## 8. Utilisation manuelle de l'API (facultatif)

Identifiants : `admin` / `password`.

Se connecter pour obtenir un token :

```bash
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

Faire une prédiction (remplacer `<TOKEN>` par le jeton reçu) :

```bash
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"input_data": {"gre_score": 337, "toefl_score": 118, "university_rating": 4, "sop": 4.5, "lor": 4.5, "cgpa": 9.65, "research": 1}}'
```

Réponse obtenue :

```json
{"prediction": 0.9583926000036933}
```

La documentation Swagger est disponible sur <http://localhost:3000>.

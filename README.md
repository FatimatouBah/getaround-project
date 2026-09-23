# GetAround — Delay Analysis & Pricing Optimization

Projet de data analysis, dashboard et machine learning réalisé dans le cadre de la formation Jedha, pour le compte fictif de GetAround.

## 🎯 Objectif

Aider le Product Manager à décider du **seuil** et du **périmètre** (toutes les voitures ou Connect uniquement) d'un délai minimum obligatoire entre deux locations, pour réduire les retards de checkin subis par les conducteurs — et proposer un modèle de prédiction du prix de location optimal.

## 🔗 Liens

- **Dashboard en ligne** : https://getaround-project-hhrtsoolqpkz9tdp9gdxya.streamlit.app/
- **API en ligne** : https://getaround-project-2.onrender.com (documentation interactive sur `/docs`)

⚠️ L'API est hébergée sur le plan gratuit de Render : elle se met en veille après 15 minutes d'inactivité. Le premier appel après une pause peut prendre 30 à 60 secondes le temps qu'elle redémarre.

## 📊 Données

- `get_around_delay_analysis.xlsx` — 21 310 locations, avec retards au checkout et enchaînements entre locations
- `get_around_pricing_project.csv` — 4 843 véhicules avec leurs caractéristiques et prix de location journalier

## 🛠️ Outils

- **Python** (pandas, scikit-learn, matplotlib)
- **Streamlit** pour le dashboard interactif, déployé sur **Streamlit Community Cloud**
- **FastAPI** pour l'API de prédiction, déployée avec **Docker** sur **Render**

## 📁 Structure du repo

```
├── dashboard/
│   ├── GetAround_Delay_Analysis.ipynb   # Notebook EDA complet
│   ├── dashboard.py                     # Dashboard Streamlit
│   ├── get_around_delay_analysis.xlsx
│   └── requirements.txt
├── api/
│   ├── app.py                           # API FastAPI
│   ├── price_model.joblib               # Modèle entraîné (Random Forest)
│   ├── requirements.txt
│   └── Dockerfile
└── README.md
```

## 🔍 Analyse des retards — résultats clés

- **8.6%** des locations sont directement enchaînées à une location précédente sur le même véhicule
- **12.6%** de ces locations enchaînées causent un vrai retard de checkin pour le conducteur suivant (retard médian : **26.5 minutes**)
- **Recommandation** : un seuil de **60 à 90 minutes**, appliqué **uniquement aux voitures Connect**, résout **70 à 80%** des cas problématiques tout en n'affectant qu'environ **1%** de l'ensemble des locations (et donc du revenu)

## 🏆 Modèle de pricing

- **Random Forest Regressor** : R² = 0.73, MAE ≈ 11 €/jour sur le jeu de test
- Variables utilisées : marque, kilométrage, puissance moteur, carburant, couleur, type de véhicule, et équipements (GPS, climatisation, boîte automatique, Connect, régulateur de vitesse, pneus hiver, parking privé)

## 🚀 Utilisation de l'API

```bash
curl -i -H "Content-Type: application/json" -X POST -d '{"input": [["Citroën", 140411, 100, "diesel", "black", "convertible", true, false, false, false, true, true, true]]}' https://getaround-project-2.onrender.com/predict
```

Réponse attendue :
```json
{"prediction": [103.17]}
```

## ▶️ Lancer en local

**Dashboard :**
```bash
cd dashboard
pip install -r requirements.txt
streamlit run dashboard.py
```

**API :**
```bash
cd api
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

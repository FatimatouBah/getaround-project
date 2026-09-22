import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Union

# ----------------------------------------------------------------
# Chargement du modele au demarrage
# ----------------------------------------------------------------
model = joblib.load("price_model.joblib")

FEATURE_ORDER = [
    "model_key", "mileage", "engine_power", "fuel", "paint_color", "car_type",
    "private_parking_available", "has_gps", "has_air_conditioning", "automatic_car",
    "has_getaround_connect", "has_speed_regulator", "winter_tires",
]

# ----------------------------------------------------------------
# Application FastAPI (le titre/description apparaissent sur /docs)
# ----------------------------------------------------------------
app = FastAPI(
    title="GetAround Pricing API",
    description=(
        "API de prediction du prix de location journalier optimal d'un vehicule, "
        "a partir de ses caracteristiques (marque, kilometrage, equipements...).\n\n"
        "Le modele est une Random Forest entrainee sur des donnees historiques de location GetAround "
        "(R2 = 0.74, MAE = 10.7 EUR/jour sur le jeu de test)."
    ),
    version="1.0.0",
)


class PredictionInput(BaseModel):
    input: List[List[Union[str, int, float, bool]]] = Field(
        ...,
        description=(
            "Liste de vehicules a estimer. Chaque vehicule est une liste de 13 valeurs, "
            "dans cet ordre exact : "
            "[model_key (str), mileage (int), engine_power (int), fuel (str), "
            "paint_color (str), car_type (str), private_parking_available (bool), "
            "has_gps (bool), has_air_conditioning (bool), automatic_car (bool), "
            "has_getaround_connect (bool), has_speed_regulator (bool), winter_tires (bool)]"
        ),
        json_schema_extra={
            "example": [
                ["Citroën", 140411, 100, "diesel", "black", "convertible",
                 True, False, False, False, True, True, True]
            ]
        },
    )


class PredictionOutput(BaseModel):
    prediction: List[float]


@app.get("/", tags=["Health"])
def read_root():
    """Verifie que l'API est en ligne."""
    return {"status": "GetAround Pricing API is up and running. See /docs for usage."}


@app.post("/predict", response_model=PredictionOutput, tags=["Prediction"])
def predict(payload: PredictionInput):
    """
    Predit le prix de location journalier optimal pour un ou plusieurs vehicules.

    - **input**: liste de vehicules, chacun represente par une liste de 13 valeurs
      (voir l'ordre exact dans la description du champ).

    Retourne une liste de prix predits (en euros par jour), dans le meme ordre que les vehicules fournis.
    """
    df = pd.DataFrame(payload.input, columns=FEATURE_ORDER)

    bool_cols = ["private_parking_available", "has_gps", "has_air_conditioning",
                 "automatic_car", "has_getaround_connect", "has_speed_regulator", "winter_tires"]
    for col in bool_cols:
        df[col] = df[col].astype(int)

    predictions = model.predict(df)
    return {"prediction": predictions.round(2).tolist()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

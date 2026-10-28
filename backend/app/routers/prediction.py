
from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Prediction"])

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml" / "prediction"

model = joblib.load(
    MODEL_DIR / "findmypark_xgboost_60min.pkl"
)

preprocessor = joblib.load(
    MODEL_DIR / "findmypark_preprocessor_60min.pkl"
)


class PredictionRequest(BaseModel):
    location: str = Field(min_length=1)
    capacity: float = Field(gt=0)
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    month: int = Field(ge=1, le=12)
    is_weekend: int = Field(ge=0, le=1)
    current_occupancy: float = Field(ge=0)


@router.post("/predict")
def predict(data: PredictionRequest):
    if data.current_occupancy > data.capacity:
        raise HTTPException(
            status_code=400,
            detail="Current occupancy cannot exceed capacity"
        )

    input_data = pd.DataFrame([{
        "SystemCodeNumber": data.location,
        "Capacity": data.capacity,
        "Hour": data.hour,
        "DayOfWeek": data.day_of_week,
        "Month": data.month,
        "IsWeekend": data.is_weekend,
        "Occupancy": data.current_occupancy,
    }])

    try:
        encoded_input = preprocessor.transform(input_data)
        prediction = float(model.predict(encoded_input)[0])
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check model files and input features."
        ) from error

    occupied = round(
        max(0, min(prediction, data.capacity))
    )

    return {
        "location": data.location,
        "forecast_horizon_minutes": 60,
        "current_occupied": round(data.current_occupancy),
        "predicted_occupied": occupied,
        "predicted_available": int(data.capacity) - occupied,
    }

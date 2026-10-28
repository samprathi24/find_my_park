import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Parking predictions"])

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml" / "prediction"
model = joblib.load(MODEL_DIR / "findmypark_xgboost_60min.pkl")
preprocessor = joblib.load(MODEL_DIR / "findmypark_preprocessor_60min.pkl")
LONDON_TIME = ZoneInfo("Europe/London")
STALE_AFTER_SECONDS = 300

PARKING_SITES = (
    {
        "id": "Bull Ring",
        "name": "Bull Ring",
        "lat": 52.4778,
        "lng": -1.8944,
        "capacity": 3053,
    },
    {
        "id": "Broad Street",
        "name": "Broad Street",
        "lat": 52.4762,
        "lng": -1.9084,
        "capacity": 690,
    },
    {
        "id": "NIA Car Parks",
        "name": "Arena Birmingham Car Parks",
        "lat": 52.4796,
        "lng": -1.9144,
        "capacity": 1268,
    },
    {
        "id": "NIA North",
        "name": "Arena Birmingham North",
        "lat": 52.4810,
        "lng": -1.9142,
        "capacity": 480,
    },
    {
        "id": "NIA South",
        "name": "Arena Birmingham South",
        "lat": 52.4775,
        "lng": -1.9145,
        "capacity": 788,
    },
)
PARKING_SITE_BY_ID = {site["id"]: site for site in PARKING_SITES}
latest_detections: dict[str, dict] = {}


class PredictionRequest(BaseModel):
    location: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    month: int = Field(ge=1, le=12)
    is_weekend: int = Field(ge=0, le=1)
    current_occupancy: float = Field(ge=0, allow_inf_nan=False)


class DetectionUpdate(BaseModel):
    location: str = Field(min_length=1)
    occupied_spaces: int = Field(ge=0)
    detected_at: datetime | None = None

    @field_validator("detected_at")
    @classmethod
    def require_timezone_for_detection_time(
        cls, value: datetime | None
    ) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("detected_at must include a timezone")
        return value


class PredictionResponse(BaseModel):
    location: str
    forecast_horizon_minutes: int
    current_occupied: int
    predicted_occupied: int
    predicted_available: int


def _predict_occupancy(
    location: str,
    capacity: int,
    current_occupancy: float,
    observed_at: datetime,
) -> PredictionResponse:
    local_time = observed_at.astimezone(LONDON_TIME)
    input_data = pd.DataFrame(
        [
            {
                "SystemCodeNumber": location,
                "Capacity": capacity,
                "Hour": local_time.hour,
                "DayOfWeek": local_time.weekday(),
                "Month": local_time.month,
                "IsWeekend": int(local_time.weekday() >= 5),
                "Occupancy": current_occupancy,
            }
        ]
    )

    try:
        encoded_input = preprocessor.transform(input_data)
        prediction = float(model.predict(encoded_input)[0])
    except Exception as error:
        logger.exception("Parking occupancy prediction failed for %s", location)
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Check model files and input features.",
        ) from error

    if not math.isfinite(prediction):
        logger.error("Model returned a non-finite prediction for %s", location)
        raise HTTPException(
            status_code=500,
            detail="Prediction failed because the model returned an invalid value.",
        )

    predicted_occupied = round(max(0, min(prediction, capacity)))
    return PredictionResponse(
        location=location,
        forecast_horizon_minutes=60,
        current_occupied=round(current_occupancy),
        predicted_occupied=predicted_occupied,
        predicted_available=capacity - predicted_occupied,
    )


@router.get("/parking")
def get_parking_status() -> dict:
    now = datetime.now(timezone.utc)
    lots = []
    for site in PARKING_SITES:
        detection = latest_detections.get(site["id"])
        if detection is None:
            lots.append(
                {
                    **site,
                    "current_occupancy": None,
                    "free_slots": None,
                    "predicted_occupied": None,
                    "predicted_available": None,
                    "detected_at": None,
                    "detection_status": "waiting_for_yolo",
                }
            )
            continue

        age_seconds = (now - detection["detected_at"]).total_seconds()
        is_stale = age_seconds > STALE_AFTER_SECONDS
        lots.append(
            {
                **site,
                "current_occupancy": detection["current_occupancy"],
                "free_slots": site["capacity"] - detection["current_occupancy"],
                "predicted_occupied": detection["prediction"].predicted_occupied,
                "predicted_available": detection["prediction"].predicted_available,
                "detected_at": detection["detected_at"],
                "detection_status": "stale" if is_stale else "live",
            }
        )

    return {"lots": lots, "forecast_horizon_minutes": 60}


@router.post("/detections", response_model=PredictionResponse)
def submit_yolo_detection(data: DetectionUpdate) -> PredictionResponse:
    site = PARKING_SITE_BY_ID.get(data.location)
    if site is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown Birmingham parking location.",
        )
    if data.occupied_spaces > site["capacity"]:
        raise HTTPException(
            status_code=400,
            detail="Detected occupied spaces cannot exceed parking capacity.",
        )

    detected_at = data.detected_at or datetime.now(timezone.utc)
    prediction = _predict_occupancy(
        location=site["id"],
        capacity=site["capacity"],
        current_occupancy=data.occupied_spaces,
        observed_at=detected_at,
    )
    latest_detections[site["id"]] = {
        "current_occupancy": data.occupied_spaces,
        "detected_at": detected_at.astimezone(timezone.utc),
        "prediction": prediction,
    }
    return prediction


@router.post("/predict", response_model=PredictionResponse)
def predict(data: PredictionRequest) -> PredictionResponse:
    if data.current_occupancy > data.capacity:
        raise HTTPException(
            status_code=400,
            detail="Current occupancy cannot exceed capacity",
        )

    observed_at = datetime.now(LONDON_TIME).replace(
        month=data.month,
        day=1,
        hour=data.hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    observed_at = observed_at.replace(
        day=1 + ((data.day_of_week - observed_at.weekday()) % 7)
    )
    return _predict_occupancy(
        location=data.location,
        capacity=data.capacity,
        current_occupancy=data.current_occupancy,
        observed_at=observed_at,
    )

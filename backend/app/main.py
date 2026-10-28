from fastapi import FastAPI
from app.routers.prediction import router as prediction_router

app = FastAPI(title="FindMyPark API")
app.include_router(prediction_router)


@app.get("/")
def root():
    return {"message": "FindMyPark backend is running!"}
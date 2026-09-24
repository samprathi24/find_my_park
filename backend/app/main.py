from fastapi import FastAPI

app = FastAPI(title="FindMyPark API")


@app.get("/")
def root():
    return {"message": "FindMyPark backend is running!"}
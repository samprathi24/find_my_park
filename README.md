
# FindMyPark

FindMyPark is a Smart Parking Management System designed to help users find suitable parking locations efficiently.

## Project Objectives

- Detect occupied and available parking spaces using YOLO and OpenCV.
- Predict future parking availability using historical and current data.
- Recommend suitable parking locations based on availability, prediction and distance.
- Visualize parking locations using OpenStreetMap and Leaflet.js.
- Develop a Digital Twin prototype for parking-space visualization.

## Technology Stack

- Frontend: React.js and JavaScript
- Backend: Python and FastAPI
- Computer Vision: YOLO and OpenCV
- Prediction: Scikit-learn
- Database: MongoDB
- Maps: OpenStreetMap and Leaflet.js

## Project Structure

- `frontend/` — Web interface and map visualization
- `backend/` — APIs and AI/ML modules
- `database/` — Database-related configuration and documentation
- `docs/` — Project documentation

## Development Status

Initial project setup in progress.

## Setup Instructions

### Backend

From the project directory, start the FastAPI server:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m pip install -r requirements-ml.txt
python -m uvicorn app.main:app --reload
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to the backend on port
`8000`.

### Birmingham parking and YOLO integration

The map uses five Birmingham locations and capacities from the
[UCI Birmingham Parking dataset](https://archive.ics.uci.edu/dataset/482/parking+birmingham).
Map coordinates are approximate points for those locations.
The model forecasts occupancy 60 minutes ahead using the location, capacity,
UK local time, and the latest YOLO occupancy count.

The detection API expects the YOLO pipeline to count occupied parking spaces
for one of the model's Birmingham location names and post that count:

```http
POST http://127.0.0.1:8000/api/detections
Content-Type: application/json
```

```json
{
  "location": "Bull Ring",
  "occupied_spaces": 125,
  "detected_at": "2026-10-28T08:30:00+00:00"
}
```

Supported `location` values are `Bull Ring`, `Broad Street`, `NIA Car Parks`,
`NIA North`, and `NIA South`. `occupied_spaces` must be a count of occupied
parking spaces from YOLO, not a count of detected vehicles unless each vehicle
is known to occupy exactly one space. `detected_at` is optional and, when
provided, must include a timezone.

For example, after the YOLO code has calculated the count:

```python
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

payload = json.dumps({
    "location": "Bull Ring",
    "occupied_spaces": occupied_spaces_from_yolo,
    "detected_at": datetime.now(timezone.utc).isoformat(),
}).encode("utf-8")
request = Request(
    "http://127.0.0.1:8000/api/detections",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(request, timeout=10) as response:
    print(response.read().decode("utf-8"))
```

The frontend polls `GET /api/parking` every five seconds and shows a forecast
only after a location has received YOLO data. Readings older than five minutes
are marked stale. Latest readings are currently held in backend memory and are
cleared when the backend restarts.

The repository's `backend/app/ml/detection/yolo_infer.py` is still empty: this
API is the handoff point for a YOLO detector, not an image/video detector by
itself. Connect the detector's per-location occupied-space count to the POST
request above. The XGBoost model uses Birmingham historical training data;
validate its forecast accuracy before using its output for real parking
decisions.

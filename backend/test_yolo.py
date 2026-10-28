import requests
from datetime import datetime, timezone
from ultralytics import YOLO

API_URL = "http://127.0.0.1:8000/api/detections"
LOCATION = "Test Lot"          # must match the location name the frontend/backend uses
IMAGE = "parking_lot.jpg"

model = YOLO("yolo26s.pt")


def count_vehicles(source):
    results = model.predict(
        source=source,
        classes=[2, 3, 5, 7],   # car, motorcycle, bus, truck
        conf=0.25,
        imgsz=1280,
        save=True,
        verbose=False,
    )
    return len(results[0].boxes), results[0].save_dir


def send_detection(count):
    payload = {
        "location": LOCATION,
        "occupied_spaces": count,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    count, save_dir = count_vehicles(IMAGE)
    print("Vehicles detected:", count)
    print("Saved to:", save_dir)

    try:
        reply = send_detection(count)
        print("Sent to backend:", reply)
    except requests.exceptions.ConnectionError:
        print("Backend is not running. Start it on port 8001 first.")
    except requests.exceptions.HTTPError as e:
        print("Backend rejected the data:", e.response.status_code, e.response.text)

import sys
import json
from pathlib import Path

import cv2
import numpy as np

# Locate the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.detection.yolo_infer import VehicleDetector

# Load slot configuration
CONFIG_PATH = Path(__file__).parent / "slot_config.json"
IMAGE_PATH = BACKEND_DIR / "parking_lot.jpg"

with open(CONFIG_PATH, "r") as file:
    config = json.load(file)

slots = config["slots"]

# Load image and detect vehicles
image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

detector = VehicleDetector()
detections = detector.detect(str(IMAGE_PATH))

print(f"\nVehicles detected by YOLO: {len(detections)}\n")

occupied_count = 0
available_count = 0

# Check each parking slot

# Check each parking slot using bounding-box overlap
OCCUPANCY_THRESHOLD = 0.15

for slot in slots:
    polygon = np.array(slot["polygon"], dtype="int32")

    # Create a mask representing the parking slot
    slot_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillPoly(slot_mask, [polygon], 255)

    slot_area = cv2.countNonZero(slot_mask)
    max_overlap = 0.0

    for vehicle in detections:
        x1, y1, x2, y2 = vehicle["bbox"]

        # Convert bounding-box coordinates to integers
        x1, y1, x2, y2 = map(
            int, [x1, y1, x2, y2]
        )

        # Keep coordinates within image boundaries
        x1 = max(0, min(x1, image.shape[1] - 1))
        x2 = max(0, min(x2, image.shape[1] - 1))
        y1 = max(0, min(y1, image.shape[0] - 1))
        y2 = max(0, min(y2, image.shape[0] - 1))

        if x2 <= x1 or y2 <= y1:
            continue

        # Create a mask for the detected vehicle
        vehicle_mask = np.zeros(
            image.shape[:2], dtype=np.uint8
        )

        cv2.rectangle(
            vehicle_mask,
            (x1, y1),
            (x2, y2),
            255,
            -1
        )

        # Calculate the overlapping area
        overlap_mask = cv2.bitwise_and(
            slot_mask, vehicle_mask
        )

        overlap_area = cv2.countNonZero(overlap_mask)

        overlap_ratio = overlap_area / slot_area

        max_overlap = max(max_overlap, overlap_ratio)

    # Decide occupancy using the overlap threshold
    if max_overlap >= OCCUPANCY_THRESHOLD:
        status = "OCCUPIED"
        occupied_count += 1
        color = (0, 0, 255)
    else:
        status = "AVAILABLE"
        available_count += 1
        color = (0, 255, 0)

    # Draw parking slot and status
    cv2.polylines(image, [polygon], True, color, 2)

    x, y = slot["polygon"][0]

    cv2.putText(
        image,
        f"{slot['id']}: {status}",
        (x, y - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1
    )

    print(
        f"{slot['id']}: {status} "
        f"(overlap: {max_overlap:.1%})"
    )


print("\n----- PARKING SUMMARY -----")
print(f"Total slots: {len(slots)}")
print(f"Occupied: {occupied_count}")
print(f"Available: {available_count}")

# Display annotated parking image
cv2.imshow("Parking Slot Occupancy", image)
print("\nPress any key on the image window to close it.")
cv2.waitKey(0)
cv2.destroyAllWindows()

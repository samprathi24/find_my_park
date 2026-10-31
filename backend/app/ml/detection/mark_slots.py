import cv2
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR.parents[2] / "parking_lot.jpg"
CONFIG_PATH = BASE_DIR / "slot_config.json"

image = cv2.imread(str(IMAGE_PATH))

if image is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

display = image.copy()
current_points = []
# Load previously saved slots so we can add more
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as file:
        slots = json.load(file)["slots"]
else:
    slots = []


def draw():
    global display
    display = image.copy()

    # Draw completed slots
    for slot in slots:
        pts = slot["polygon"]
        cv2.polylines(
            display,
            [__import__("numpy").array(pts, dtype="int32")],
            True, (0, 255, 0), 2
        )
        x, y = pts[0]
        cv2.putText(
            display, slot["id"], (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

    # Draw current slot points
    for point in current_points:
        cv2.circle(display, tuple(point), 5, (0, 0, 255), -1)

    if len(current_points) > 1:
        import numpy as np
        cv2.polylines(
            display,
            [np.array(current_points, dtype="int32")],
            False, (0, 0, 255), 2
        )

    cv2.putText(
        display,
        f"Slot: S{len(slots) + 1} | Points: {len(current_points)}/4",
        (20, 30), cv2.FONT_HERSHEY_SIMPLEX,
        0.8, (255, 0, 0), 2
    )

    cv2.imshow("Parking Slot Marker", display)


def mouse_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(current_points) < 4:
        current_points.append([x, y])
        draw()


cv2.namedWindow("Parking Slot Marker")
cv2.setMouseCallback("Parking Slot Marker", mouse_click)

print("Click four corners of each parking slot.")
print("N = next slot | U = undo point | S = save and exit")

draw()

while True:
    key = cv2.waitKey(20) & 0xFF

    if key == ord("n"):
        if len(current_points) == 4:
            slots.append({
                "id": f"S{len(slots) + 1}",
                "polygon": current_points.copy()
            })
            current_points.clear()
            print(f"Slot S{len(slots)} marked!")
            draw()
        else:
            print("Please click exactly 4 corners first.")

    elif key == ord("u"):
        if current_points:
            current_points.pop()
            draw()

    elif key == ord("s"):
        if current_points:
            print("Finish or undo the current slot before saving.")
            continue

        config = {
            "image_width": image.shape[1],
            "image_height": image.shape[0],
            "slots": slots
        }

        with open(CONFIG_PATH, "w") as file:
            json.dump(config, file, indent=4)

        print(f"Saved {len(slots)} slots to {CONFIG_PATH}")
        break

    elif key == ord("q"):
        print("Exited without saving.")
        break

cv2.destroyAllWindows()
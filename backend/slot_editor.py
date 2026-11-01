
import json
from pathlib import Path

import cv2


BACKEND_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BACKEND_DIR / "parking_lot.jpg"
CONFIG_PATH = (
    BACKEND_DIR / "app" / "ml" / "detection" / "slot_config.json"
)


class ParkingSlotEditor:
    def __init__(self):
        self.image = cv2.imread(str(IMAGE_PATH))

        if self.image is None:
            raise FileNotFoundError(
                f"Parking image not found: {IMAGE_PATH}"
            )

        with CONFIG_PATH.open("r", encoding="utf-8") as file:
            self.config = json.load(file)

        self.slots = self.config.get("slots", [])
        self.points = []
        self.window_name = "FindMyPark - Slot Editor"

    def draw(self):
        display = self.image.copy()

        # Draw previously saved slots.
        for slot in self.slots:
            polygon = slot["points"]
            for index, point in enumerate(polygon):
                next_point = polygon[(index + 1) % len(polygon)]
                cv2.line(
                    display, tuple(point), tuple(next_point),
                    (0, 255, 0), 2
                )

            center_x = int(
                sum(point[0] for point in polygon) / len(polygon)
            )
            center_y = int(
                sum(point[1] for point in polygon) / len(polygon)
            )
            cv2.putText(
                display, slot["id"], (center_x, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

        # Draw points for the slot currently being created.
        for point in self.points:
            cv2.circle(display, tuple(point), 5, (0, 0, 255), -1)

        for index in range(1, len(self.points)):
            cv2.line(
                display, tuple(self.points[index - 1]),
                tuple(self.points[index]), (0, 0, 255), 2
            )

        cv2.putText(
            display,
            f"Slots: {len(self.slots)} | Points: {len(self.points)}/4",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2
        )
        cv2.putText(
            display,
            "Click corners | N: next slot | U: undo | R: reset | S: save | Q: quit",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )

        cv2.imshow(self.window_name, display)

    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(self.points) < 4:
            self.points.append([x, y])
            self.draw()

    def save(self):
        self.config["slots"] = self.slots

        with CONFIG_PATH.open("w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=2)

        print(f"Saved {len(self.slots)} slots to {CONFIG_PATH}")

    def run(self):
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.on_mouse)
        self.draw()

        while True:
            key = cv2.waitKey(20) & 0xFF

            if key == ord("u") and self.points:
                self.points.pop()
                self.draw()

            elif key == ord("r"):
                self.points.clear()
                self.draw()

            elif key == ord("n"):
                if len(self.points) != 4:
                    print("Select exactly four corners first.")
                    continue

                slot_id = f"S{len(self.slots) + 1}"
                self.slots.append({
                    "id": slot_id,
                    "points": self.points.copy()
                })
                self.points.clear()
                self.draw()
                print(f"Added {slot_id}")

            elif key == ord("s"):
                self.save()

            elif key == ord("q"):
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    ParkingSlotEditor().run()

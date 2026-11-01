
from pathlib import Path

import cv2
import numpy as np

from app.ml.detection.yolo_infer import VehicleDetector
from app.ml.detection.occupancy import ParkingOccupancy


class ParkingVisualizer:
    """Visualize vehicle detections and parking-slot occupancy."""

    def __init__(self, detector=None, occupancy=None):
        self.detector = detector or VehicleDetector()
        self.occupancy = occupancy or ParkingOccupancy()

    def visualize(self, image_path, output_path=None, show=False):
        image_path = Path(image_path)
        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Could not load image: {image_path}"
            )

        detections = self.detector.detect(str(image_path))
        result = self.occupancy.estimate_occupancy(detections)

        inside_vehicles = result["vehicles"]
        inside_ids = {id(vehicle) for vehicle in inside_vehicles}

        # Draw the overall parking-region boundary.
        region = self.occupancy.region.reshape((-1, 1, 2))
        cv2.polylines(
            image, [region], True, (255, 120, 0), 3
        )

        # Draw YOLO vehicle detections.
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection["bbox"])

            inside = id(detection) in inside_ids
            color = (0, 200, 0) if inside else (0, 0, 255)

            label = (
                f"{detection['label']} "
                f"{detection['confidence']:.2f}"
            )

            cv2.rectangle(
                image, (x1, y1), (x2, y2), color, 2
            )

            cv2.putText(
                image,
                label,
                (x1, max(y1 - 5, 85)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA,
            )

        # Draw individual parking slots and their status.
        for slot_result in result["slots"]:
            slot_id = slot_result["id"]

            slot_config = next(
                slot for slot in self.occupancy.slots
                if slot["id"] == slot_id
            )

            polygon = np.array(
                slot_config["points"], dtype=np.int32
            ).reshape((-1, 1, 2))

            if slot_result["occupied"]:
                color = (0, 0, 255)       # Red: occupied
                status = "OCCUPIED"
            else:
                color = (0, 255, 0)       # Green: free
                status = "FREE"

            cv2.polylines(
                image, [polygon], True, color, 3
            )

            center_x = int(
                np.mean(polygon[:, 0, 0])
            )
            center_y = int(
                np.mean(polygon[:, 0, 1])
            )

            cv2.putText(
                image,
                f"{slot_id}: {status}",
                (center_x - 45, center_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                2,
                cv2.LINE_AA,
            )

        # Display vehicle and slot summaries.
        header_height = 100
        cv2.rectangle(
            image,
            (0, 0),
            (image.shape[1], header_height),
            (35, 35, 35),
            -1,
        )

        cv2.putText(
            image,
            "FindMyPark | Parking Occupancy",
            (15, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            image,
            f"Vehicles: {len(detections)} | "
            f"Inside region: {result['detected_vehicles_inside']}",
            (15, 51),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            image,
            f"Slots: {result['total_slots']} | "
            f"Occupied: {result['occupied_slots']} | "
            f"Free: {result['free_slots']}",
            (15, 78),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        saved_path = None

        if output_path is not None:
            saved_path = Path(output_path)
            saved_path.parent.mkdir(
                parents=True, exist_ok=True
            )

            if not cv2.imwrite(str(saved_path), image):
                raise IOError(
                    f"Could not save image: {saved_path}"
                )

        if show:
            cv2.imshow("FindMyPark - Parking Occupancy", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return {
            "image": image,
            "detections": detections,
            "vehicle_count": len(detections),
            "inside_count": result["detected_vehicles_inside"],
            "outside_count": (
                len(detections)
                - result["detected_vehicles_inside"]
            ),
            "total_slots": result["total_slots"],
            "occupied_slots": result["occupied_slots"],
            "free_slots": result["free_slots"],
            "slots": result["slots"],
            "output_path": (
                str(saved_path) if saved_path else None
            ),
        }

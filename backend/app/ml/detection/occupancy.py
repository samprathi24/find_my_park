
import json
from pathlib import Path

import cv2
import numpy as np


CONFIG_PATH = Path(__file__).resolve().parent / "slot_config.json"


class ParkingOccupancy:
    """Estimate parking-slot occupancy using YOLO vehicle detections."""

    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = Path(config_path)

        with self.config_path.open("r", encoding="utf-8") as file:
            self.config = json.load(file)

        self.region = np.array(
            self.config["parking_region"],
            dtype=np.int32,
        )

        self.slots = self.config.get("slots", [])

        if len(self.region) < 3:
            raise ValueError(
                "The parking region must contain at least 3 points."
            )

        for slot in self.slots:
            if len(slot.get("points", [])) < 3:
                raise ValueError(
                    f"Slot {slot.get('id', 'unknown')} "
                    "must contain at least 3 points."
                )

    def is_inside_region(self, detection):
        """Check whether a vehicle's bottom-center point is inside."""
        x1, y1, x2, y2 = detection["bbox"]

        center_x = int((x1 + x2) / 2)
        bottom_y = int(y2)

        return cv2.pointPolygonTest(
            self.region,
            (center_x, bottom_y),
            False,
        ) >= 0

    @staticmethod
    def _intersection_over_slot(vehicle_bbox, slot_polygon):
        """Calculate the fraction of a slot covered by a vehicle box."""
        x1, y1, x2, y2 = map(float, vehicle_bbox)

        vehicle_polygon = np.array(
            [
                [x1, y1],
                [x2, y1],
                [x2, y2],
                [x1, y2],
            ],
            dtype=np.float32,
        )

        slot_polygon = np.asarray(
            slot_polygon,
            dtype=np.float32,
        )

        slot_area = abs(cv2.contourArea(slot_polygon))

        if slot_area <= 0:
            return 0.0

        intersection_area, _ = cv2.intersectConvexConvex(
            slot_polygon,
            vehicle_polygon,
        )

        return float(intersection_area / slot_area)

    def estimate_occupancy(self, detections):
        """Estimate occupancy for every configured parking slot."""
        vehicles_inside = [
            detection
            for detection in detections
            if self.is_inside_region(detection)
        ]

        slot_results = []

        for slot in self.slots:
            best_overlap = 0.0
            matched_vehicle = None

            for detection in detections:
                overlap = self._intersection_over_slot(
                    detection["bbox"],
                    slot["points"],
                )

                if overlap > best_overlap:
                    best_overlap = overlap
                    matched_vehicle = detection

            # Initial threshold; we'll tune it after visual testing.
            occupied = best_overlap >= 0.15

            slot_results.append(
                {
                    "id": slot["id"],
                    "occupied": occupied,
                    "status": "OCCUPIED" if occupied else "FREE",
                    "overlap": round(best_overlap, 3),
                    "vehicle": matched_vehicle if occupied else None,
                }
            )

        occupied_count = sum(
            slot["occupied"] for slot in slot_results
        )

        total_slots = len(slot_results)

        return {
            "detected_vehicles_inside": len(vehicles_inside),
            "vehicles": vehicles_inside,
            "slots": slot_results,
            "total_slots": total_slots,
            "occupied_slots": occupied_count,
            "free_slots": total_slots - occupied_count,
        }

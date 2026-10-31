
from pathlib import Path

from ultralytics import YOLO


# Locate the backend directory and YOLO model.
BACKEND_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BACKEND_DIR / "yolo26s.pt"

# COCO class IDs: car=2, motorcycle=3, bus=5, truck=7.
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class VehicleDetector:
    """Detect vehicles in parking-lot images using YOLO."""

    def __init__(self, model_path=MODEL_PATH, confidence=0.25, image_size=1280):
        self.model_path = Path(model_path)
        self.confidence = confidence
        self.image_size = image_size

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"YOLO model not found: {self.model_path}"
            )

        # Load the model once and reuse it for subsequent predictions.
        self.model = YOLO(str(self.model_path))

    def detect(self, image):
        """
        Detect vehicles in an image.

        Args:
            image: Image path or an image array supported by Ultralytics.

        Returns:
            A list of dictionaries containing bounding boxes,
            confidence scores, and vehicle labels.
        """
        results = self.model.predict(
            source=image,
            classes=list(VEHICLE_CLASSES.keys()),
            conf=self.confidence,
            imgsz=self.image_size,
            verbose=False,
        )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                class_id = int(box.cls[0].item())

                detections.append(
                    {
                        "label": VEHICLE_CLASSES[class_id],
                        "class_id": class_id,
                        "confidence": float(box.conf[0].item()),
                        "bbox": [
                            float(value)
                            for value in box.xyxy[0].tolist()
                        ],
                    }
                )

        return detections


from ultralytics import YOLO

model = YOLO("yolo26s.pt")

results = model.predict(
    source="parking_lot.jpg",
    classes=[2, 3, 5, 7],
    conf=0.25,
    imgsz=1280,
    save=True
)

print("\nAll detected objects:")
for box in results[0].boxes:
    class_id = int(box.cls[0])
    confidence = float(box.conf[0])
    print(
        model.names[class_id],
        "confidence:",
        round(confidence, 3)
    )

print("Vehicles detected:", len(results[0].boxes))
print("Saved to:", results[0].save_dir)

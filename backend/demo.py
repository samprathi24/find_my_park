
import streamlit as st
import cv2
import numpy as np
from PIL import Image

from app.ml.detection.yolo_infer import VehicleDetector

st.set_page_config(
    page_title="FindMyPark",
    page_icon="🅿️",
    layout="wide",
)

st.title("🅿️ FindMyPark")
st.subheader("AI-Powered Parking Detection")
st.write("Upload a parking-lot image to detect vehicles.")

@st.cache_resource
def load_detector():
    return VehicleDetector()

uploaded_file = st.file_uploader(
    "Upload a parking image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_array = np.array(image)

    with st.spinner("Detecting vehicles..."):
        detector = load_detector()
        detections = detector.detect(image_array)

    annotated = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["bbox"])
        label = (
            f"{detection['label']} "
            f"{detection['confidence']:.2f}"
        )

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            (0, 200, 0),
            2,
        )

        cv2.putText(
            annotated,
            label,
            (x1, max(y1 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 200, 0),
            1,
            cv2.LINE_AA,
        )

    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

    col1, col2 = st.columns(2)

    with col1:
        st.image(image_array, caption="Original image", use_container_width=True)

    with col2:
        st.image(annotated, caption="YOLO vehicle detections", use_container_width=True)

    st.metric("Vehicles detected", len(detections))

    st.caption(
        "Vehicle detections are not the same as occupied parking bays. "
        "Free-slot counts require parking-space capacity and reliable "
        "slot-level occupancy classification."
    )
else:
    st.info("Upload a parking image to get started.")

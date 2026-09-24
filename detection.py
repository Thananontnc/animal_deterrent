"""YOLOv8 object detection.

Wraps the ultralytics model and returns plain Detection objects, so no other
module needs to know about ultralytics types.
"""

from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2) in pixels


class Detector:
    def __init__(self, model_path, class_names, min_confidence, image_size=640):
        """Load the model and limit detection to `class_names`.

        `min_confidence` is the lowest confidence YOLO reports. Per-class
        thresholds are applied later in decision.py.
        """
        self.model = YOLO(model_path)
        self.min_confidence = min_confidence
        self.image_size = image_size

        name_to_id = {name: idx for idx, name in self.model.names.items()}
        unknown = [name for name in class_names if name not in name_to_id]
        if unknown:
            raise ValueError(
                f"Classes {unknown} are not in the model. "
                f"Valid names: {sorted(name_to_id)}"
            )
        self.class_ids = [name_to_id[name] for name in class_names]

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run the model on one BGR frame and return its detections."""
        result = self.model.predict(
            frame,
            conf=self.min_confidence,
            classes=self.class_ids,
            imgsz=self.image_size,
            verbose=False,
        )[0]

        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    class_name=result.names[int(box.cls[0])],
                    confidence=float(box.conf[0]),
                    bbox=(x1, y1, x2, y2),
                )
            )
        return detections

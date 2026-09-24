"""Frame sources: a webcam, a video file, or a still image.

main.py reads frames through `open_source`, so moving to the Raspberry Pi
camera only means adding a source here (see README.md).
"""

from pathlib import Path

import cv2

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class OpenCVSource:
    """A webcam (int index) or a video file (path) via cv2.VideoCapture."""

    def __init__(self, source):
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video source {source!r}")

    def read(self):
        """Return the next BGR frame, or None when no frame is available."""
        ok, frame = self.capture.read()
        return frame if ok else None

    def release(self):
        self.capture.release()


class ImageSource:
    """Returns the same still image on every read. Useful for testing."""

    def __init__(self, path):
        self.frame = cv2.imread(str(path))
        if self.frame is None:
            raise RuntimeError(f"Could not read image {path!r}")

    def read(self):
        return self.frame.copy()

    def release(self):
        pass


def open_source(source):
    """Open `source`: an int webcam index, an image path, or a video path."""
    if isinstance(source, int):
        return OpenCVSource(source)
    if Path(source).suffix.lower() in IMAGE_EXTENSIONS:
        return ImageSource(source)
    return OpenCVSource(source)

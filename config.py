"""All tunable constants for the animal deterrent, in one place.

Edit values here rather than in the other modules.
"""

# --- Detection -------------------------------------------------------------

# YOLO weights file. ultralytics downloads it automatically on first run.
MODEL_PATH = "yolov8n.pt"

# Image size YOLO resizes frames to. 640 is the model default; 320 is
# roughly 3-4x faster and is worth trying on the Raspberry Pi 5.
IMAGE_SIZE = 640

# COCO class names that count as "animals to spray". Must match names in the
# model exactly (see detection.py for the check). Other COCO animals:
# "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe".
ANIMAL_CLASSES = ["cat", "dog", "bird"]

PERSON_CLASS = "person"

# Minimum confidence for an animal detection to trigger a spray.
CONFIDENCE_THRESHOLD = 0.5

# Minimum confidence for a person detection to pause the system. Kept lower
# than CONFIDENCE_THRESHOLD on purpose: when unsure whether someone is in the
# yard, it is safer to not spray.
PERSON_CONFIDENCE_THRESHOLD = 0.3

# --- Decision timing (seconds) ---------------------------------------------

# After a SPRAY, no new SPRAY is allowed for this long.
SPRAY_COOLDOWN_SECONDS = 5.0

# After the last person leaves the frame, wait this long before a SPRAY is
# allowed again.
PERSON_DEBOUNCE_SECONDS = 20.0

# How long the valve stays open for each spray.
SPRAY_DURATION_SECONDS = 2.0

# --- Camera ----------------------------------------------------------------

# Webcam device index for cv2.VideoCapture. 0 is the laptop's built-in camera.
CAMERA_INDEX = 0

# --- Aiming ----------------------------------------------------------------

# Flip these if the servo moves the wrong way once mounted.
INVERT_PAN = False
INVERT_TILT = False

# --- Hardware backend ------------------------------------------------------

# "mock" prints actions. Add a "pi" backend in hardware.py for the real rig.
HARDWARE_BACKEND = "mock"

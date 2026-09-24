"""All tunable constants for the animal deterrent, in one place.

Edit values here rather than in the other modules.
"""

# --- Detection -------------------------------------------------------------

# YOLO weights file. ultralytics downloads it automatically on first run.
# yolo11s was the most accurate of 8 setups tested on garden dog and cat
# videos (dog found in 85% of frames, cat in 95%; yolov8n: 62% and 39%).
# If the Pi is too slow, use "yolo26n.pt" with IMAGE_SIZE = 960 (see PI_SETUP.md).
MODEL_PATH = "yolo11s.pt"

# Image size YOLO resizes frames to. Larger finds far-away animals better
# but runs slower.
IMAGE_SIZE = 640

# COCO class names that count as "animals to spray". Must match names in the
# model exactly (see detection.py for the check). Other COCO animals:
# "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe".
ANIMAL_CLASSES = ["cat", "dog"]

PERSON_CLASS = "person"

# On a Raspberry Pi, convert the model once to NCNN format and use that.
# NCNN runs several times faster than the default PyTorch model on ARM CPUs.
# Has no effect on Windows or Mac.
USE_NCNN_ON_RASPBERRY_PI = True

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

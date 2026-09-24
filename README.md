# Animal Deterrent

A camera watches the yard and a YOLO11s model looks for animals. If it sees
an animal and no person is in frame, the system aims a nozzle at the animal
and sprays water.

The code currently runs on a laptop with its webcam. The servos and valve are
mocked: they print what they would do. It is written to move to a
Raspberry Pi 5 with few changes (see [Connecting real hardware](#connecting-real-hardware)).

## Files

| File | What it does |
|------|--------------|
| `config.py` | Every tunable value: animal classes, confidence thresholds, cooldown, debounce, spray duration, camera index, model file, servo direction. |
| `detection.py` | Loads the YOLO model (ultralytics). On a Raspberry Pi it converts the model once to the faster NCNN format. `Detector.detect(frame)` returns a list of `Detection(class_name, confidence, bbox=(x1, y1, x2, y2))`. Only reports the animal classes and `person`. |
| `targeting.py` | `bbox_center(bbox)` gives the target pixel. `pan_tilt_offset(...)` turns that pixel into a pan/tilt offset from the frame center, each from -1.0 to 1.0. |
| `decision.py` | `DecisionEngine.update(detections, w, h)` returns `PAUSE`, `SPRAY` (with target) or `IDLE`. It applies the person rule, the cooldown and the debounce. |
| `hardware.py` | The `Hardware` interface (`aim`, `spray`, `stop_spray`, `close`) and `MockHardware`, which only prints. |
| `camera.py` | Frame sources: webcam, video file, or still image. |
| `main.py` | The live loop. Reads frames, runs detection and decision, calls the hardware, and shows the annotated video window. |
| `test_decision.py` | Unit tests for the decision rules and timing, using a fake clock. |
| `evaluate.py` | Measures detection accuracy on a video clip: detection rate, confidence, misses, false positives, and how many sprays would fire. |
| `requirements.txt` | Pinned versions of `ultralytics` and `opencv-python`. |
| `TESTING.md` | Step-by-step live test plan using a phone as the camera. |
| `PI_SETUP.md` | Step-by-step Raspberry Pi 5 setup, from a blank SD card to a first test. |

## Decision rules

Checked in this order, every frame:

1. A person is in frame: **PAUSE**. Any spray in progress stops.
2. A person left the frame less than `PERSON_DEBOUNCE_SECONDS` (20 s) ago: **PAUSE**.
3. An animal is in frame but the last spray was less than `SPRAY_COOLDOWN_SECONDS` (5 s) ago: **IDLE**.
4. An animal is in frame: **SPRAY** at the center of the most confident animal.
5. Otherwise: **IDLE**.

A person needs only 0.30 confidence to pause the system
(`PERSON_CONFIDENCE_THRESHOLD`). An animal needs 0.50 to trigger a spray
(`CONFIDENCE_THRESHOLD`). The person threshold is lower on purpose: when the
model is unsure whether someone is there, the system does not spray.

The window shows one of three states: `IDLE`, `PAUSED` or `SPRAYING`.
`SPRAYING` stays on screen for `SPRAY_DURATION_SECONDS` after each spray.

## Setup

Needs Python 3.10 or newer.

Windows (PowerShell):

```powershell
git clone https://github.com/Thananontnc/animal_deterrent.git
cd animal_deterrent
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux / Raspberry Pi:

```bash
git clone https://github.com/Thananontnc/animal_deterrent.git
cd animal_deterrent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first run downloads `yolo11s.pt` (about 18 MB) into the current folder.

## Running

```bash
python main.py                          # laptop webcam
python main.py --source path/to/cat.jpg # a still image, repeated every frame
python main.py --source path/to/yard.mp4
python main.py --headless               # no window, prints state changes only
python main.py --max-frames 100         # stop after 100 frames
```

Press `q` in the video window, or close the window, to quit. In headless
mode, press Ctrl+C.

The terminal prints every state change and every mock hardware action:

```
[21:10:04] SPRAYING: cat 0.93
AIM to pan=-0.30 tilt=+0.12
SPRAY for 2s
```

Run the decision tests:

```bash
python -m unittest test_decision -v
```

## Measuring accuracy on a video

Put the clip in the project folder, then run:

```bash
python evaluate.py test_dog.mp4 --expect dog
python evaluate.py test_cat.mp4 --expect cat --save test_cat_annotated.mp4
```

It prints:

- **Spray-level detection:** frames where the animal scored at least
  `CONFIDENCE_THRESHOLD`.
- **Weak only:** frames where the model saw the animal, but not confidently
  enough to spray. Many weak frames suggest lowering `CONFIDENCE_THRESHOLD`.
- **Not detected at all:** possible misses.
- **Longest stretch without a spray-level detection:** how long the animal
  could stay in the yard untouched.
- **Other classes detected:** a cat called a dog (harmless, since it still
  sprays), or a false `person` (it pauses the system).
- **Sprays the system would fire:** counted in video time.

The script assumes the animal is in view for the whole clip. Frames where it
walks out of view count as misses. Use `--save` and watch the annotated video
to check.

## No webcam? Use your phone as the camera

`--source` also accepts a network stream URL. Phone camera apps stream
MJPEG over Wi-Fi, and OpenCV reads that directly.

1. Connect the phone and the PC to the same Wi-Fi network.
2. Install a camera streaming app and start it:
   - Android: **IP Webcam**. The URL is `http://PHONE_IP:8080/video`.
   - Android or iPhone: **DroidCam**. The URL is `http://PHONE_IP:4747/video`.
     DroidCam serves one viewer at a time, so close any other DroidCam
     client first.
3. The app shows the phone's IP address. Run:

   ```bash
   python main.py --source http://192.168.1.23:8080/video
   ```

The stream has some lag. It is fine for checking behavior, but it is slower
than a real camera.

## Testing the animal path without an animal

The webcam will mostly see you, so it will mostly show `PAUSED`. To test the
spray path:

- **Still photo:** `python main.py --source cat.jpg`. Expect `SPRAYING`, then
  `IDLE` with a cooldown countdown, then `SPRAYING` again every 5 s. A
  known-good test photo with two cats:
  http://images.cocodataset.org/val2017/000000039769.jpg
- **Video:** `python main.py --source test_dog.mp4`. Any cat or dog clip
  works. To measure accuracy on a clip, use `evaluate.py` (below).
- **Phone or monitor held up to the webcam:** show a cat photo on your phone
  with your own body out of frame. This tests the real camera path. If any
  part of you is visible, the system pauses, which is correct.
- **Person plus animal:** use a photo with both a person and a dog. Expect
  `PAUSED`.
- **Debounce:** step into frame, step out, then show an animal. The window
  shows `PAUSED` with a countdown for 20 s before any spray.

To test faster, lower `SPRAY_COOLDOWN_SECONDS` and `PERSON_DEBOUNCE_SECONDS`
in `config.py`.

## Connecting real hardware

`main.py` and `decision.py` only use the `Hardware` interface in
`hardware.py`. To drive the real rig:

1. Write a class in `hardware.py` that subclasses `Hardware`.
2. Add it to `create_hardware()`, for example `if backend == "pi": return PiHardware()`.
3. Set `HARDWARE_BACKEND = "pi"` in `config.py`.

Starting point for a PCA9685 servo driver plus a relay on a GPIO pin. **This
sketch is untested.** Check pins, channels and angles against your wiring.

```python
# pip install adafruit-circuitpython-servokit gpiozero lgpio
import threading

from adafruit_servokit import ServoKit
from gpiozero import OutputDevice

PAN_CHANNEL, TILT_CHANNEL = 0, 1
PAN_ANGLES = (0, 180)    # servo angle at pan -1.0 and +1.0
TILT_ANGLES = (60, 120)  # servo angle at tilt -1.0 and +1.0
VALVE_PIN = 17           # BCM pin that drives the relay


def offset_to_angle(offset, angles):
    low, high = angles
    return low + (offset + 1) / 2 * (high - low)


class PiHardware(Hardware):
    def __init__(self):
        self.kit = ServoKit(channels=16)
        # Many relay boards switch on a LOW signal. If so, set active_high=False.
        self.valve = OutputDevice(VALVE_PIN, active_high=True, initial_value=False)
        self.timer = None

    def aim(self, pan, tilt):
        self.kit.servo[PAN_CHANNEL].angle = offset_to_angle(pan, PAN_ANGLES)
        self.kit.servo[TILT_CHANNEL].angle = offset_to_angle(tilt, TILT_ANGLES)

    def spray(self, duration_seconds):
        self.stop_spray()
        self.valve.on()
        self.timer = threading.Timer(duration_seconds, self.valve.off)
        self.timer.start()  # returns at once, so the camera loop keeps running

    def stop_spray(self):
        if self.timer:
            self.timer.cancel()
        self.valve.off()
```

Notes for the Raspberry Pi 5:

- **GPIO library:** `RPi.GPIO` does not work on the Pi 5. Use `gpiozero`
  (with the `lgpio` backend), as above.
- **I2C:** enable I2C for the PCA9685 with `sudo raspi-config`.
- **Power:** do not power the servos or the solenoid from the Pi's 5 V pin.
  Give them their own supply and connect the grounds. Put a flyback diode
  across the solenoid, unless your relay module already has one.
- **Aim calibration:** the pan/tilt offset says where the animal is in the
  camera image. How that maps to servo angles depends on how the camera and
  nozzle are mounted. Tune `PAN_ANGLES` and `TILT_ANGLES` by spraying at
  known spots. Use `INVERT_PAN` and `INVERT_TILT` in `config.py` if a servo
  moves the wrong way.
- **Camera:** a USB webcam works as is with `CAMERA_INDEX = 0`. The Pi
  Camera Module needs `picamera2` instead of `cv2.VideoCapture`. Add a
  `Picamera2Source` class to `camera.py` with the same `read()` and
  `release()` methods, and return it from `open_source()`. Install picamera2
  with `sudo apt install python3-picamera2`. Then create the venv with
  `python3 -m venv --system-site-packages .venv` so the venv can see it.
- **Speed:** on the Pi, the model is converted automatically to NCNN on the
  first run (`USE_NCNN_ON_RASPBERRY_PI` in `config.py`). NCNN is several
  times faster on ARM processors. If it is still too slow, see "If it is too
  slow" in `PI_SETUP.md`.
- **No monitor:** run `python main.py --headless` over SSH or as a service.

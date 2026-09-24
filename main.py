"""Live loop: camera -> detection -> decision -> hardware, with a video overlay.

Usage:
    python main.py                      # laptop webcam (config.CAMERA_INDEX)
    python main.py --source cat.jpg     # still image, repeated every frame
    python main.py --source yard.mp4    # video file
    python main.py --headless           # no window; log state changes only

Press 'q' in the video window to quit (Ctrl+C in headless mode).
"""

import argparse
import time

import cv2

import config
from camera import open_source
from decision import Action, DecisionEngine
from detection import Detector, is_raspberry_pi
from hardware import create_hardware

WINDOW_NAME = "Animal Deterrent"
BANNER_HEIGHT = 62

# BGR colors
STATE_COLORS = {"IDLE": (160, 160, 160), "PAUSED": (0, 200, 255), "SPRAYING": (0, 0, 255)}
PERSON_COLOR = (0, 200, 0)
ANIMAL_COLOR = (0, 0, 255)


def parse_args():
    parser = argparse.ArgumentParser(description="Garden animal deterrent")
    parser.add_argument(
        "--source",
        default=str(config.CAMERA_INDEX),
        help="webcam index, image path, or video path (default: config.CAMERA_INDEX)",
    )
    parser.add_argument("--headless", action="store_true", help="do not open a video window")
    parser.add_argument("--max-frames", type=int, default=0, help="stop after N frames (0 = run forever)")
    args = parser.parse_args()
    args.source = int(args.source) if args.source.isdigit() else args.source
    return args


def draw_overlay(frame, detections, state, reason, target, fps):
    for d in detections:
        color = PERSON_COLOR if d.class_name == config.PERSON_CLASS else ANIMAL_COLOR
        x1, y1, x2, y2 = d.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{d.class_name} {d.confidence:.2f}"
        # Put the label above the box, or inside it if the banner would cover it.
        label_y = y1 - 6 if y1 - 6 > BANNER_HEIGHT + 14 else max(y1, BANNER_HEIGHT) + 20
        cv2.putText(frame, label, (x1 + 4, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    if target is not None:
        x, y = int(target[0]), int(target[1])
        cv2.drawMarker(frame, (x, y), STATE_COLORS["SPRAYING"], cv2.MARKER_CROSS, 40, 3)

    color = STATE_COLORS[state]
    cv2.rectangle(frame, (0, 0), (frame.shape[1], BANNER_HEIGHT), (0, 0, 0), -1)
    cv2.putText(frame, state, (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    cv2.putText(frame, reason, (10, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"{fps:.1f} FPS", (frame.shape[1] - 100, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    args = parse_args()

    detector = Detector(
        config.MODEL_PATH,
        [*config.ANIMAL_CLASSES, config.PERSON_CLASS],
        min(config.CONFIDENCE_THRESHOLD, config.PERSON_CONFIDENCE_THRESHOLD),
        config.IMAGE_SIZE,
        use_ncnn=config.USE_NCNN_ON_RASPBERRY_PI and is_raspberry_pi(),
    )
    engine = DecisionEngine(
        animal_classes=config.ANIMAL_CLASSES,
        person_class=config.PERSON_CLASS,
        animal_threshold=config.CONFIDENCE_THRESHOLD,
        person_threshold=config.PERSON_CONFIDENCE_THRESHOLD,
        cooldown_seconds=config.SPRAY_COOLDOWN_SECONDS,
        debounce_seconds=config.PERSON_DEBOUNCE_SECONDS,
        invert_pan=config.INVERT_PAN,
        invert_tilt=config.INVERT_TILT,
    )
    hardware = create_hardware(config.HARDWARE_BACKEND)
    source = open_source(args.source)

    spraying_until = 0.0
    spray_target = None
    last_state = None
    fps = 0.0
    frame_count = 0
    last_frame_time = time.monotonic()

    try:
        while True:
            frame = source.read()
            if frame is None:
                print("No more frames from source; exiting.")
                break

            height, width = frame.shape[:2]
            detections = detector.detect(frame)
            decision = engine.update(detections, width, height)
            now = time.monotonic()

            if decision.action is Action.SPRAY:
                hardware.aim(*decision.pan_tilt)
                hardware.spray(config.SPRAY_DURATION_SECONDS)
                spraying_until = now + config.SPRAY_DURATION_SECONDS
                spray_target = decision.target
            elif decision.action is Action.PAUSE and now < spraying_until:
                hardware.stop_spray()
                spraying_until = 0.0

            if decision.action is Action.PAUSE:
                state = "PAUSED"
            elif now < spraying_until:
                state = "SPRAYING"
            else:
                state = "IDLE"

            if state != last_state:
                print(f"[{time.strftime('%H:%M:%S')}] {state}: {decision.reason}")
                last_state = state

            elapsed = now - last_frame_time
            last_frame_time = now
            if elapsed > 0:
                fps = 1 / elapsed if fps == 0 else 0.9 * fps + 0.1 / elapsed

            if not args.headless:
                target = spray_target if state == "SPRAYING" else None
                draw_overlay(frame, detections, state, decision.reason, target, fps)
                cv2.imshow(WINDOW_NAME, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break  # window closed with the X button

            frame_count += 1
            if args.max_frames and frame_count >= args.max_frames:
                break
    except KeyboardInterrupt:
        pass
    finally:
        source.release()
        hardware.close()
        cv2.destroyAllWindows()
        print(f"Stopped after {frame_count} frames.")


if __name__ == "__main__":
    main()

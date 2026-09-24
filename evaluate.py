"""Measure how well the model detects one animal class in a video clip.

Usage:
    python evaluate.py test_dog.mp4 --expect dog
    python evaluate.py test_cat.mp4 --expect cat --save test_cat_annotated.mp4

Reports, per clip:
  - how many frames have the expected animal at spray-level confidence
  - weak detections (seen, but below CONFIDENCE_THRESHOLD, so no spray)
  - frames with no detection at all (possible misses)
  - the longest stretch without a spray-level detection
  - other classes detected (cat/dog mix-ups, false persons)
  - how many sprays the decision logic would fire, in video time

It assumes the animal is in view for the whole clip. If it walks out of
frame, those frames count as misses, so check them in the --save video.
"""

import argparse
import statistics
import time
from collections import defaultdict

import cv2

import config
from decision import Action, DecisionEngine
from detection import Detector, is_raspberry_pi
from main import draw_overlay

# Report detections down to this confidence, to show near misses below the
# spray threshold.
REPORT_FLOOR = 0.10


def parse_args():
    parser = argparse.ArgumentParser(description="Measure detection accuracy on a video")
    parser.add_argument("video", help="path to the video file")
    parser.add_argument("--expect", required=True, choices=config.ANIMAL_CLASSES,
                        help="the animal that is in the video")
    parser.add_argument("--save", help="write an annotated copy of the video to this path")
    parser.add_argument("--model", default=config.MODEL_PATH,
                        help="model to test, e.g. yolov8s.pt (default: config.MODEL_PATH)")
    parser.add_argument("--image-size", type=int, default=config.IMAGE_SIZE,
                        help="YOLO input size, e.g. 960 (default: config.IMAGE_SIZE)")
    parser.add_argument("--ncnn", action="store_true",
                        help="use the NCNN model even when not on a Raspberry Pi")
    return parser.parse_args()


def longest_run(flags):
    """Return (length, start_index) of the longest run of True in `flags`."""
    best_len, best_start, run_len = 0, 0, 0
    for i, flag in enumerate(flags):
        run_len = run_len + 1 if flag else 0
        if run_len > best_len:
            best_len, best_start = run_len, i - run_len + 1
    return best_len, best_start


def main():
    args = parse_args()

    capture = cv2.VideoCapture(args.video)
    if not capture.isOpened():
        raise SystemExit(f"Could not open video {args.video!r}")
    video_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0

    detector = Detector(
        args.model,
        [*config.ANIMAL_CLASSES, config.PERSON_CLASS],
        REPORT_FLOOR,
        args.image_size,
        use_ncnn=args.ncnn or (config.USE_NCNN_ON_RASPBERRY_PI and is_raspberry_pi()),
    )

    # Run the decision logic on video time, not wall-clock time, so the
    # spray count does not depend on how fast this PC processes frames.
    frame_index = 0
    engine = DecisionEngine(
        animal_classes=config.ANIMAL_CLASSES,
        person_class=config.PERSON_CLASS,
        animal_threshold=config.CONFIDENCE_THRESHOLD,
        person_threshold=config.PERSON_CONFIDENCE_THRESHOLD,
        cooldown_seconds=config.SPRAY_COOLDOWN_SECONDS,
        debounce_seconds=config.PERSON_DEBOUNCE_SECONDS,
        clock=lambda: frame_index / video_fps,
    )

    writer = None
    best_conf = []                   # best expected-class confidence per frame, 0.0 if none
    any_animal = 0                   # frames with any animal class at spray level
    other_frames = defaultdict(int)  # class -> number of frames it appeared in
    other_max = defaultdict(float)   # class -> highest confidence seen
    spray_times = []
    spraying_until = -1.0
    spray_target = None
    started = time.monotonic()

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        now = frame_index / video_fps
        height, width = frame.shape[:2]

        detections = detector.detect(frame)
        expected = [d.confidence for d in detections if d.class_name == args.expect]
        best_conf.append(max(expected, default=0.0))
        any_animal += any(
            d.class_name in config.ANIMAL_CLASSES and d.confidence >= config.CONFIDENCE_THRESHOLD
            for d in detections
        )
        for name in {d.class_name for d in detections} - {args.expect}:
            other_frames[name] += 1
        for d in detections:
            if d.class_name != args.expect:
                other_max[d.class_name] = max(other_max[d.class_name], d.confidence)

        decision = engine.update(detections, width, height)
        if decision.action is Action.SPRAY:
            spray_times.append(now)
            spraying_until = now + config.SPRAY_DURATION_SECONDS
            spray_target = decision.target

        if args.save:
            if writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(args.save, fourcc, video_fps, (width, height))
            if decision.action is Action.PAUSE:
                state = "PAUSED"
            elif now < spraying_until:
                state = "SPRAYING"
            else:
                state = "IDLE"
            target = spray_target if state == "SPRAYING" else None
            draw_overlay(frame, detections, state, decision.reason, target, video_fps)
            writer.write(frame)

        frame_index += 1

    capture.release()
    if writer is not None:
        writer.release()

    total = len(best_conf)
    if total == 0:
        raise SystemExit("The video has no readable frames.")

    threshold = config.CONFIDENCE_THRESHOLD
    strong = sum(c >= threshold for c in best_conf)
    weak = sum(0 < c < threshold for c in best_conf)
    missed = sum(c == 0 for c in best_conf)
    gap_len, gap_start = longest_run([c < threshold for c in best_conf])
    seen = [c for c in best_conf if c > 0]
    elapsed = time.monotonic() - started

    def pct(n):
        return f"{100 * n / total:.1f}%"

    print()
    print(f"Video:     {args.video}  ({total} frames, {total / video_fps:.1f} s at {video_fps:.0f} fps)")
    print(f"Expected:  {args.expect}  (spray threshold {threshold:.2f})")
    print(f"Model:     {args.model} at image size {args.image_size}")
    print(f"Processed: {total / elapsed:.1f} frames/s on this machine")
    print()
    print(f"Any animal class at spray level: {any_animal:>5} frames  {pct(any_animal)}"
          "  (what triggers a spray)")
    print(f"{args.expect} at spray level (>= {threshold:.2f}):  {strong:>5} frames  {pct(strong)}")
    print(f"{args.expect} weak only ({REPORT_FLOOR:.2f}-{threshold:.2f}):  {weak:>5} frames  {pct(weak)}")
    print(f"{args.expect} not detected at all:     {missed:>5} frames  {pct(missed)}")
    if gap_len:
        print(f"Longest stretch without a spray-level detection: "
              f"{gap_len / video_fps:.1f} s (from {gap_start / video_fps:.1f} s)")
    print()
    if seen:
        print(f"Confidence of {args.expect} when seen: min {min(seen):.2f}  "
              f"median {statistics.median(seen):.2f}  "
              f"mean {statistics.mean(seen):.2f}  max {max(seen):.2f}")
    else:
        print(f"{args.expect} was never detected.")
    print()
    if other_frames:
        print("Other classes detected (possible false positives):")
        for name in sorted(other_frames, key=other_frames.get, reverse=True):
            if name == config.PERSON_CLASS:
                note = "counts as a person if >= %.2f: pauses the system" % config.PERSON_CONFIDENCE_THRESHOLD
            else:
                note = "another animal class: still sprays if >= %.2f" % threshold
            print(f"  {name:<8} {other_frames[name]:>5} frames, max conf {other_max[name]:.2f}  ({note})")
    else:
        print("Other classes detected: none")
    print()
    times = ", ".join(f"{t:.1f}s" for t in spray_times) or "none"
    print(f"Sprays the system would fire: {len(spray_times)}  (at {times})")
    if args.save:
        print(f"Annotated video: {args.save}")


if __name__ == "__main__":
    main()

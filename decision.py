"""Spray / pause / idle decision logic.

Rules, in priority order:
  1. A person in frame                          -> PAUSE
  2. A person left less than the debounce ago   -> PAUSE
  3. An animal in frame, cooldown still running -> IDLE
  4. An animal in frame                         -> SPRAY at the most confident animal
  5. Otherwise                                  -> IDLE
"""

import time
from dataclasses import dataclass
from enum import Enum

from targeting import bbox_center, pan_tilt_offset


class Action(Enum):
    IDLE = "IDLE"
    PAUSE = "PAUSE"
    SPRAY = "SPRAY"


@dataclass
class Decision:
    action: Action
    reason: str
    target: tuple[float, float] | None = None     # pixel (x, y); set for SPRAY only
    pan_tilt: tuple[float, float] | None = None   # normalized; set for SPRAY only


class DecisionEngine:
    def __init__(
        self,
        animal_classes,
        person_class,
        animal_threshold,
        person_threshold,
        cooldown_seconds,
        debounce_seconds,
        invert_pan=False,
        invert_tilt=False,
        clock=time.monotonic,
    ):
        self.animal_classes = set(animal_classes)
        self.person_class = person_class
        self.animal_threshold = animal_threshold
        self.person_threshold = person_threshold
        self.cooldown_seconds = cooldown_seconds
        self.debounce_seconds = debounce_seconds
        self.invert_pan = invert_pan
        self.invert_tilt = invert_tilt
        self.clock = clock

        self.last_spray_time = None
        self.last_person_time = None

    def update(self, detections, frame_width, frame_height):
        """Decide what to do for one frame's detections."""
        now = self.clock()

        if any(
            d.class_name == self.person_class and d.confidence >= self.person_threshold
            for d in detections
        ):
            self.last_person_time = now
            return Decision(Action.PAUSE, "person in frame")

        if self.last_person_time is not None:
            since_person = now - self.last_person_time
            if since_person < self.debounce_seconds:
                left = self.debounce_seconds - since_person
                return Decision(Action.PAUSE, f"person left, resume in {left:.0f}s")

        animals = [
            d for d in detections
            if d.class_name in self.animal_classes and d.confidence >= self.animal_threshold
        ]
        if not animals:
            return Decision(Action.IDLE, "nothing detected")

        best = max(animals, key=lambda d: d.confidence)

        if self.last_spray_time is not None:
            since_spray = now - self.last_spray_time
            if since_spray < self.cooldown_seconds:
                left = self.cooldown_seconds - since_spray
                return Decision(Action.IDLE, f"{best.class_name} seen, cooldown {left:.1f}s")

        self.last_spray_time = now
        target = bbox_center(best.bbox)
        pan_tilt = pan_tilt_offset(
            target, frame_width, frame_height, self.invert_pan, self.invert_tilt
        )
        return Decision(
            Action.SPRAY,
            f"{best.class_name} {best.confidence:.2f}",
            target=target,
            pan_tilt=pan_tilt,
        )

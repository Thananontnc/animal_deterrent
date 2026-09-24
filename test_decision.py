"""Tests for decision.py timing rules, using a fake clock (no camera needed).

Run:  python -m unittest test_decision -v
"""

import unittest

from decision import Action, DecisionEngine
from detection import Detection

W, H = 640, 480
CAT = Detection("cat", 0.9, (500, 100, 600, 200))
WEAK_CAT = Detection("cat", 0.4, (0, 0, 10, 10))
DOG = Detection("dog", 0.7, (0, 0, 100, 100))
PERSON = Detection("person", 0.8, (0, 0, 100, 400))
WEAK_PERSON = Detection("person", 0.35, (0, 0, 100, 400))


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make_engine(clock):
    return DecisionEngine(
        animal_classes=["cat", "dog", "bird"],
        person_class="person",
        animal_threshold=0.5,
        person_threshold=0.3,
        cooldown_seconds=5.0,
        debounce_seconds=20.0,
        clock=clock,
    )


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.engine = make_engine(self.clock)

    def decide(self, *detections):
        return self.engine.update(list(detections), W, H)

    def test_idle_when_nothing(self):
        self.assertIs(self.decide().action, Action.IDLE)

    def test_spray_at_most_confident_animal(self):
        d = self.decide(DOG, CAT)
        self.assertIs(d.action, Action.SPRAY)
        self.assertEqual(d.target, (550.0, 150.0))
        pan, tilt = d.pan_tilt
        self.assertAlmostEqual(pan, 0.71875)   # right of center
        self.assertAlmostEqual(tilt, 0.375)    # above center

    def test_person_pauses_even_with_animal(self):
        self.assertIs(self.decide(CAT, PERSON).action, Action.PAUSE)

    def test_low_confidence_person_still_pauses(self):
        self.assertIs(self.decide(CAT, WEAK_PERSON).action, Action.PAUSE)

    def test_low_confidence_animal_ignored(self):
        self.assertIs(self.decide(WEAK_CAT).action, Action.IDLE)

    def test_cooldown_blocks_second_spray(self):
        self.assertIs(self.decide(CAT).action, Action.SPRAY)
        self.clock.now += 4.9
        self.assertIs(self.decide(CAT).action, Action.IDLE)
        self.clock.now += 0.2
        self.assertIs(self.decide(CAT).action, Action.SPRAY)

    def test_debounce_after_person_leaves(self):
        self.assertIs(self.decide(PERSON).action, Action.PAUSE)
        self.clock.now += 19.9
        self.assertIs(self.decide(CAT).action, Action.PAUSE)
        self.clock.now += 0.2
        self.assertIs(self.decide(CAT).action, Action.SPRAY)

    def test_person_returning_restarts_debounce(self):
        self.decide(PERSON)
        self.clock.now += 15
        self.decide(PERSON)
        self.clock.now += 15
        self.assertIs(self.decide(CAT).action, Action.PAUSE)


if __name__ == "__main__":
    unittest.main()

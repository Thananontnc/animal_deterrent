"""Hardware interface for the aiming servos and the spray valve.

main.py only talks to the `Hardware` interface. To drive real hardware,
write a subclass (see README.md, "Connecting real hardware"), register it in
`create_hardware`, and set HARDWARE_BACKEND in config.py. decision.py and
main.py do not change.
"""

from abc import ABC, abstractmethod


class Hardware(ABC):
    @abstractmethod
    def aim(self, pan: float, tilt: float) -> None:
        """Point the nozzle. pan and tilt are in [-1.0, 1.0] (see targeting.py)."""

    @abstractmethod
    def spray(self, duration_seconds: float) -> None:
        """Open the valve for `duration_seconds`, then close it.

        Must return immediately (use a timer or thread in a real
        implementation) so the camera loop keeps running.
        """

    @abstractmethod
    def stop_spray(self) -> None:
        """Close the valve now. Called when a person appears mid-spray."""

    def close(self) -> None:
        """Release hardware and leave the valve closed. Called on exit."""
        self.stop_spray()


class MockHardware(Hardware):
    """Prints what real hardware would do."""

    def aim(self, pan, tilt):
        print(f"AIM to pan={pan:+.2f} tilt={tilt:+.2f}")

    def spray(self, duration_seconds):
        print(f"SPRAY for {duration_seconds:g}s")

    def stop_spray(self):
        print("STOP spray")


def create_hardware(backend: str) -> Hardware:
    if backend == "mock":
        return MockHardware()
    raise ValueError(f"Unknown HARDWARE_BACKEND {backend!r}")

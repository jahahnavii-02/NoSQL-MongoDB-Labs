from enum import Enum
from time import monotonic


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, threshold=3, recovery_seconds=30):
        self.threshold = threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.state = State.CLOSED
        self.opened_at = 0.0

    def allow_request(self):
        if self.state == State.CLOSED:
            return True
        if self.state == State.OPEN:
            if monotonic() - self.opened_at >= self.recovery_seconds:
                self.state = State.HALF_OPEN
                return True
            return False
        return True

    def record_success(self):
        self.failures = 0
        self.state = State.CLOSED

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = State.OPEN
            self.opened_at = monotonic()

    def call(self, function, *args, **kwargs):
        if not self.allow_request():
            raise RuntimeError("Circuit breaker is open")
        try:
            result = function(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

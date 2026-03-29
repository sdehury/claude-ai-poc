import time
import threading


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rate: float = 2.0, burst: int = 5):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_time = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self):
        """Block until a token is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_time
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                self.last_time = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

            time.sleep(0.1)

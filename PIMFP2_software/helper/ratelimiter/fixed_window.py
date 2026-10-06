import math
import time
from threading import RLock

from .waiting_strategy import WaitingStrategy


class FixedWindowRateLimiter:
    """
    A thread-safe fixed window rate limiter supporting bulk permits acquisition.
    """

    NANOSECONDS_PER_MILLISECOND = 1_000_000
    MILLISECONDS_PER_SECOND = 1_000

    def __init__(self, window: int, burst: int) -> None:
        """
        Initialize the rate limiter with specified window and burst.

        Args:
            window: window in milliseconds, must be positive.
            burst: maximum permits per window, must be positive.

        Raises:
            ValueError: invalid window or burst.
        """

        if window <= 0:
            raise ValueError("window must be positive")
        if burst <= 0:
            raise ValueError("burst must be positive")

        self.window = window
        self.burst = burst
        self.available = 0
        self.last_reset = None
        self.lock = RLock()

    def acquire(self, permits: int = 1, waiting_strategy: WaitingStrategy = WaitingStrategy.IMMEDIATE_RETURN,
                waiting_timeout: int = 0) -> tuple[bool, int]:
        """
        Attempt to acquire the specified number of permits.

        The rate limiter supports three waiting strategies when insufficient permits are available:
        - IMMEDIATE_RETURN: return immediately without waiting if permits are not immediately available.
        - UNTIL_AVAILABLE: blocks the calling thread until the requested permits become available,
          potentially waiting through multiple window.
        - UNTIL_TIMEOUT: if permits become available within the specified timeout, acquires them;
          otherwise, returns after the timeout expires.

        Args:
            permits: number of permits to acquire, must be non-negative.
            waiting_strategy: strategy when insufficient permits are available, default is IMMEDIATE_RETURN.
            waiting_timeout: max waiting time in milliseconds, only used with UNTIL_TIMEOUT strategy,
            Default is 0, in which case UNTIL_TIMEOUT is equivalent to IMMEDIATE_RETURN. Must be non-negative.

        Returns:
            (allowed: bool, required_wait: int):
            - allowed: True if permits eventually acquired, False otherwise.
            - required_wait, wait time in milliseconds:
                * 0 if permits were immediately available.
                * IMMEDIATE_RETURN: estimated wait time needed to acquire permits.
                - UNTIL_AVAILABLE: actual time waited before acquiring permits.
                - UNTIL_TIMEOUT: actual time waited before acquiring permits or until timeout.

        Raises:
            ValueError: invalid permits or waiting_timeout.
            TypeError: invalid waiting_strategy.
        """

        if permits < 0:
            raise ValueError("required permits must be non-negative")
        if not isinstance(waiting_strategy, WaitingStrategy):
            raise TypeError("waiting_strategy must be WaitingStrategy")
        if waiting_timeout < 0:
            raise ValueError("waiting_timeout must be non-negative")

        with self.lock:
            monotonic_ms = time.monotonic_ns() // self.NANOSECONDS_PER_MILLISECOND

            # reset window when the first acquire or current window has expired
            if self.last_reset is None or monotonic_ms >= self.last_reset + self.window:
                self.last_reset = monotonic_ms
                self.available = self.burst

            shortage = permits - self.available
            time_overdrawn = 0
            permits_overdrawn = 0
            if shortage > 0:
                # how many full window required to accumulate enough permits
                window_overdrawn = math.ceil(shortage / self.burst)
                time_overdrawn = self.window * window_overdrawn
                permits_overdrawn = self.burst * window_overdrawn

            # when the permits are available
            available_at = self.last_reset + time_overdrawn

            # permits are available immediately
            if monotonic_ms >= available_at:
                self.available -= permits
                return True, 0

            # have to wait a while to acquire permits
            required_wait = available_at - monotonic_ms

            if waiting_strategy == WaitingStrategy.IMMEDIATE_RETURN:
                return False, required_wait

            # determine whether should waiting
            # WaitingStrategy.UNTIL_AVAILABLE: overdraft the `shortage` permits and wait for `required_wait`
            # WaitingStrategy.UNTIL_TIMEOUT:
            # - will be allowed before time out, indeed overdraft the `shortage` permits and wait for `required_wait`
            # - will time out, just wait for `waiting_timeout`
            available_before_timeout = (waiting_strategy == WaitingStrategy.UNTIL_TIMEOUT
                                        and required_wait <= waiting_timeout)
            if WaitingStrategy.UNTIL_AVAILABLE or available_before_timeout:
                self.available = self.available - permits + permits_overdrawn
                self.last_reset = available_at

        if waiting_strategy == WaitingStrategy.UNTIL_AVAILABLE:
            time.sleep(required_wait / self.MILLISECONDS_PER_SECOND)
            return True, required_wait

        if available_before_timeout:
            time.sleep(required_wait / self.MILLISECONDS_PER_SECOND)
            return True, required_wait
        else:
            time.sleep(waiting_timeout / self.MILLISECONDS_PER_SECOND)
            return False, waiting_timeout

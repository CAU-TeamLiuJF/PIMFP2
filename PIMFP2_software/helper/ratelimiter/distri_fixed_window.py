import time

import redis


class DistributedFixedWindowRateLimiter:
    """
    A distributed fixed window rate limiter base on redis supporting bulk permits acquisition.
    """

    MILLISECONDS_PER_SECOND = 1_000

    def __init__(self, redis_client: redis.Redis, window: int, burst: int, prefix: str = "distri_fw_rl") -> None:
        """
        Initialize the rate limiter with specified redis_client, window and burst.

        Args:
            redis_client: redis instance
            window: window in milliseconds, must be positive.
            burst: maximum permits per window, must be positive.
            prefix: redis key prefix, must set

        Raises:
            ValueError: invalid window, burst or prefix.
        """

        if window <= 0:
            raise ValueError("window must be positive")
        if burst <= 0:
            raise ValueError("burst must be positive")
        if not prefix:
            raise ValueError("must set prefix")

        self.redis_client = redis_client
        self.window = window
        self.burst = burst
        self.prefix = prefix

        script = f"""
        local identifier = KEYS[1]
        local permits = ARGV[1]
        local waiting_timeout = tonumber(ARGV[2])
        local window = {self.window}
        local burst = {self.burst}

        local available = redis.call('GET', identifier)
        local pttl = redis.call('PTTL', identifier)
        -- reset window when the first acquire or current window has expired
        if pttl <= 0 then
            available = burst
            pttl = window
        end

        local shortage = permits - available
        local time_overdrawn = 0
        local permits_overdrawn = 0
        if shortage > 0 then
            -- how many full window required to accumulate enough permits
            local window_overdrawn = math.ceil(shortage / burst)
            time_overdrawn = window * window_overdrawn
            permits_overdrawn = burst * window_overdrawn
        end

        local available_pttl = pttl + time_overdrawn
        local required_wait = available_pttl - window
        if required_wait <= 0 then
            redis.call('SET', identifier, available - permits, 'PX', pttl)
            return 0
        end
        
        -- return immediately without waiting if permits are not immediately available
        if waiting_timeout == 0 then
            redis.call('SET', identifier, available, 'PX', pttl)
            return required_wait
        end
        
        -- waiting until the requested permits become available
        if waiting_timeout < 0 then
            redis.call('SET', identifier, available - permits + permits_overdrawn, 'PX', available_pttl)
            return required_wait
        end

        -- waiting until the requested permits become available or time out
        if required_wait <= waiting_timeout then
            redis.call('SET', identifier, available - permits + permits_overdrawn, 'PX', available_pttl)
        else
            redis.call('SET', identifier, available, 'PX', pttl)
        end
        return required_wait
        """
        self.lua_script = self.redis_client.register_script(script)

    def try_acquire(self, identifier: str, permits: int = 1, waiting_timeout: int = 0) -> tuple[bool, int]:
        if waiting_timeout < 0:
            raise ValueError("waiting_timeout must be non-negative")

        return self._acquire(
            identifier=identifier,
            permits=permits,
            waiting_timeout=waiting_timeout
        )

    def acquire(self, identifier: str, permits: int = 1):
        return self._acquire(
            identifier=identifier,
            permits=permits,
            waiting_timeout=-1
        )

    def _acquire(self, identifier: str, permits: int, waiting_timeout: int) -> tuple[bool, int]:
        """
        Attempt to acquire the specified number of permits.

        The rate limiter supports three waiting strategies when insufficient permits are available:
        - waiting_timeout == 0 (immediately return): return immediately without waiting if permits are not immediately available.
        - waiting_timeout < 0 (until available): blocks the calling thread until the requested permits become available,
          potentially waiting through multiple window.
        - waiting_timeout > 0 (until timeout): if permits become available within the specified timeout, acquires them;
          otherwise, returns after the timeout expires.

        Args:
            identifier: identifier of the resource to acquire permits, must be non-empty.
            permits: number of permits to acquire, must be non-negative.
            waiting_timeout: waiting time in milliseconds, Default is 0, Must be non-negative.

        Returns:
            (allowed: bool, required_wait: int):
            - allowed: True if permits eventually acquired, False otherwise.
            - required_wait, wait time in milliseconds:
                * 0 if permits were immediately available.
                * immediately return: estimated wait time needed to acquire permits.
                - until available: actual time waited before acquiring permits.
                - until timeout: actual time waited before acquiring permits or until timeout.

        Raises:
            ValueError: invalid identifier or permits.
        """
        if not identifier:
            raise ValueError("identifier must be non-empty")
        if permits < 0:
            raise ValueError("required permits must be non-negative")

        required_wait = self.lua_script(
            keys=[f"{self.prefix}::{identifier}"],
            args=[permits, waiting_timeout]
        )
        if required_wait == 0:
            return True, 0

        if waiting_timeout == 0:
            return False, required_wait

        if waiting_timeout < 0:
            time.sleep(required_wait / self.MILLISECONDS_PER_SECOND)
            return True, required_wait

        if required_wait <= waiting_timeout:
            time.sleep(required_wait / self.MILLISECONDS_PER_SECOND)
            return True, required_wait
        else:
            time.sleep(waiting_timeout / self.MILLISECONDS_PER_SECOND)
            return False, waiting_timeout

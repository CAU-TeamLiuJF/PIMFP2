import threading
import time
from types import TracebackType
from typing import Optional, Type

import redis
import shortuuid


class Lock:
    _MILLISECONDS_PER_SECOND = 1_000
    _NANOSECONDS_PER_MILLISECOND = 1_000_000
    _DEFAULT_LIFE_TIME = 30 * _MILLISECONDS_PER_SECOND
    _DEFAULT_DOG_SCHEDULE = _DEFAULT_LIFE_TIME // 3

    _WATCH_DOG = """
    local value = redis.call('get', KEYS[1])
    if not value or value ~= ARGV[1] then
        return 0
    end
    local expiration = redis.call('pttl', KEYS[1])
    if not expiration then
        expiration = 0
    end
    if expiration < 0 then
        return 0
    end

    local newttl = ARGV[2]
    redis.call('pexpire', KEYS[1], newttl)
    return 1
    """

    _RELEASE = """
    local token = redis.call('get', KEYS[1])
    if not token or token ~= ARGV[1] then
        return 0
    end
    redis.call('del', KEYS[1])
    return 1
    """

    def __init__(self, r: redis.Redis, lock_name: str):
        self._r = r
        self._identifier = lock_name
        self._lua_watch_dog = self._r.register_script(self._WATCH_DOG)
        self._lua_release = self._r.register_script(self._RELEASE)
        self._local_value = threading.local()

    def acquire(self, life_time: Optional[int] = None, spin_time: int = 100):
        """
        Args:
            life_time: lock lifetime in milliseconds
            spin_time: spin time in milliseconds
        """
        value = shortuuid.uuid()
        while True:
            if self._r.set(self._identifier, value, nx=True, px=life_time or self._DEFAULT_LIFE_TIME):
                self._local_value.value = value
                break
            time.sleep(spin_time / self._MILLISECONDS_PER_SECOND)

        # watch dog
        if life_time is None:
            self._watch_dog(value)

    def try_acquire(self, timeout: int = 0, life_time: Optional[int] = None, spin_time: int = 100) -> bool:
        """
        Args:
            timeout: wait timeout in milliseconds
            life_time: lock lifetime in milliseconds
            spin_time: spin time in milliseconds
        """
        value = shortuuid.uuid()
        start = time.monotonic_ns()
        while True:
            if self._r.set(self._identifier, value, nx=True, px=life_time or self._DEFAULT_LIFE_TIME):
                self._local_value.value = value
                break
            if (time.monotonic_ns() - start) / self._NANOSECONDS_PER_MILLISECOND > timeout:
                return False
            time.sleep(spin_time / self._MILLISECONDS_PER_SECOND)

        # watch dog
        if life_time is None:
            self._watch_dog(value)
        return True

    def release(self):
        if not self._local_value.value:
            return
        self._lua_release(keys=[self._identifier], args=[self._local_value.value])
        self._local_value.value = None

    def _watch_dog(self, value: str):
        def _watch_dog_worker():
            while True:
                time.sleep(self._DEFAULT_DOG_SCHEDULE / self._MILLISECONDS_PER_SECOND)
                if not self._lua_watch_dog(keys=[self._identifier], args=[value, self._DEFAULT_LIFE_TIME]):
                    break

        threading.Thread(target=_watch_dog_worker, daemon=True, name=f"watch_dog_{self._identifier}").start()

    def __enter__(self) -> "Lock":
        self.acquire()
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        self.release()

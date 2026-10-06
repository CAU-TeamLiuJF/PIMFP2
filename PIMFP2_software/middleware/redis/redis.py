from typing import Optional, TypeVar, Type, Any, Set

import redis
from redis.typing import KeyT, ResponseT, ExpiryT, AbsExpiryT

from .serializable import Serializable

R = TypeVar('R')


class Redis(redis.Redis):
    def __init__(self, serializer: Serializable, **kwargs):
        super().__init__(**kwargs)
        self._encoding = kwargs.get("encoding", "utf-8")
        self._serializer = serializer
        self._register_delifeq()

    def _register_delifeq(self):
        self._lua_delifeq = self.register_script(
            """
            local name = KEYS[1]
            local value = ARGV[1]
            local cached_value = redis.call('GET', name)
            if value == cached_value then
                redis.call('DEL', name)
                return 1
            else
                return 0
            end
            """
        )

    def serialize(self, value: Any) -> Optional[bytes]:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, memoryview):
            return value.tobytes()
        if isinstance(value, (int, float)):
            return repr(value).encode(self._encoding)
        if isinstance(value, str):
            return value.encode(self._encoding)
        return self._serializer.serialize(value)

    def deserialize(self, value: Optional[bytes], type: Type[R]) -> R:
        if value is None:
            return None
        if type == bytes:
            return value
        if type == memoryview:
            return memoryview(value)
        if type == int:
            return int(value.decode(self._encoding))
        if type == float:
            return float(value.decode(self._encoding))
        if type == str:
            return value.decode(self._encoding)
        return self._serializer.deserialize(value, type)

    def get(self, name: KeyT, type: Type[R] = bytes) -> R:
        value = super().get(name)
        return self.deserialize(value, type)

    def set(
            self,
            name: KeyT,
            value: Any,
            ex: Optional[ExpiryT] = None,
            px: Optional[ExpiryT] = None,
            nx: bool = False,
            xx: bool = False,
            keepttl: bool = False,
            get: bool = False,
            exat: Optional[AbsExpiryT] = None,
            pxat: Optional[AbsExpiryT] = None,
    ) -> ResponseT:
        value = self.serialize(value)
        return super().set(name, value, ex, px, nx, xx, keepttl, get, exat, pxat)

    def getex(
            self,
            name: KeyT,
            type: Type[R] = bytes,
            ex: Optional[ExpiryT] = None,
            px: Optional[ExpiryT] = None,
            exat: Optional[AbsExpiryT] = None,
            pxat: Optional[AbsExpiryT] = None,
            persist: bool = False,
    ) -> R:
        value = super().getex(name, ex, px, exat, pxat, persist)
        return self.deserialize(value, type)

    def getdel(self, name: KeyT, type: Type[R] = bytes) -> Optional[R]:
        value = super().getdel(name)
        return self.deserialize(value, type)

    def delifeq(self, name: KeyT, value: Any):
        eq = self._lua_delifeq(
            [name],
            [self.serialize(value)]
        )
        return eq == 1

    def smembers(self, name: KeyT, type: Type[R] = bytes) -> Optional[Set[R]]:
        value = super().smembers(name)
        if value is None:
            return None
        return {self.deserialize(member, type) for member in value}

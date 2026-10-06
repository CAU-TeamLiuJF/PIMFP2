from typing import Protocol, Any, TypeVar, Type, Union, runtime_checkable
import msgspec

T = TypeVar('T')


@runtime_checkable
class Serializable(Protocol):
    def serialize(self, value: Any) -> bytes:
        ...

    def deserialize(self, data: Union[bytes, memoryview], typ: Type[T]) -> T:
        ...


class MsgspecSerializer(Serializable):
    def serialize(self, value: Any) -> bytes:
        return msgspec.json.encode(value, order="sorted")

    def deserialize(self, data: Union[str, bytes, memoryview], typ: Type[T]) -> T:
        return msgspec.json.decode(data, type=typ)

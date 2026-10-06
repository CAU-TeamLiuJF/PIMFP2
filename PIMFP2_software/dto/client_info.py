from dataclasses import dataclass
from typing import Optional

import msgspec


@dataclass
class Client(msgspec.Struct, rename="camel"):
    type: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    engine: Optional[str] = None
    engine_version: Optional[str] = None


@dataclass
class OS(msgspec.Struct, rename="camel"):
    name: Optional[str] = None
    version: Optional[str] = None
    platform: Optional[str] = None


@dataclass
class Device(msgspec.Struct, rename="camel"):
    type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ClientInfo(msgspec.Struct, rename="camel"):
    client: Optional[Client] = None
    os: Optional[OS] = None
    device: Optional[Device] = None

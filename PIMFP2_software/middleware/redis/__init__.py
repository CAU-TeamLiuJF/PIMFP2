from typing import Optional

from pimfp import logger
from .redis import Redis
from .region import Region
from .serializable import Serializable, MsgspecSerializer

LOGGER = logger.get_logger(__name__)

redis: Optional[Redis] = None


def init_redis(config) -> Redis:
    """
    Initialize the redis.
    """
    global redis

    # create redis instance and test connectivity
    LOGGER.info(f"initializing redis with config:{config}")
    redis = Redis(serializer=MsgspecSerializer(), **config)
    if not redis.ping():
        LOGGER.critical("redis connection failed")
        exit(1)
    return redis


__all__ = [
    "redis",
    "Redis",
    "Serializable",
    "MsgspecSerializer",
    "Region"
]

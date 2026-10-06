from enum import Enum

_SECOND = 1
_MINUTE = 60 * _SECOND
_HOUR = 60 * _MINUTE
_DAY = 24 * _HOUR


class Region(Enum):
    SESSION = ("SESSION", 2 * _HOUR)  # session with ttl 2 hours
    REGISTER = ("REGISTER", 5 * _MINUTE)  # register with ttl 5 minutes
    LOGIN = ("LOGIN", 5 * _MINUTE)  # login with ttl 5 minutes
    REMEMBERME = ("REMEMBERME", 7 * _DAY)  # remember me with ttl 7 days
    RESET = ("RESET", 5 * _MINUTE)  # reset with ttl 5 minutes
    UPLOAD = ("UPLOAD", 10 * _MINUTE)  # upload with ttl 10 minutes
    FLOWNO = ("FLOWNO", _DAY + _MINUTE)  # flow no with ttl one day plus a redundant minute
    DAILY_STATS = ("DAILY_STATS", _DAY) # daily stats with ttl one day
    PERSIST = ("PERSIST", -1)  # persist with no expiration

    def __init__(self, region: str, ttl: int):
        super().__init__()
        self.region = region
        self.ttl = ttl

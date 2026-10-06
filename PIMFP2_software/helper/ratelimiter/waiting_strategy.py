from enum import Enum


class WaitingStrategy(Enum):
    """
    Waiting Strategy
    """

    IMMEDIATE_RETURN = "immediate_return"
    UNTIL_AVAILABLE = "until_available"
    UNTIL_TIMEOUT = "until_timeout"

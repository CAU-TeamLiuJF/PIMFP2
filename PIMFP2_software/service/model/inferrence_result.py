from dataclasses import dataclass
from enum import Enum

from typing import Optional


class FailReasonEnum(Enum):
    INVALID_IMAGE_SIZE = "INVALID_IMAGE_SIZE"
    ERROR_WHEN_OPENING = "ERROR_WHEN_OPENING"
    ERROR_WHEN_PREPROCESSING = "ERROR_WHEN_PREPROCESSING"
    ERROR_WHEN_INFERENCING = "ERROR_WHEN_INFERENCING"


@dataclass
class InferenceResult:
    value: Optional[float]
    success: bool = True
    reason: Optional[FailReasonEnum] = None

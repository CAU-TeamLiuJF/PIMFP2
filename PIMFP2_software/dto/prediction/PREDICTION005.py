from dataclasses import dataclass
from typing import Optional, Annotated

import msgspec

from pimfp.entity import PredictTaskStatus, PredictionType, UltrasoundType, PigType


@dataclass
class PREDICTION005Req(msgspec.Struct, rename="camel"):
    page_no: Annotated[int, msgspec.Meta(ge=1)]
    page_size: Annotated[int, msgspec.Meta(ge=1, le=100)]
    status: Optional[PredictTaskStatus] = None


@dataclass
class PredictTaskResultDTO(msgspec.Struct, rename="camel"):
    flow_no: str
    submit_at: str
    prediction_type: PredictionType
    ultrasound_type: UltrasoundType
    pig_type: PigType
    status: PredictTaskStatus
    completed_at: Optional[str] = None
    result: Optional[str] = None


@dataclass
class PREDICTION005Rsp(msgspec.Struct, rename="camel"):
    num: int
    total_num: int
    total_pages: int
    tasks: Optional[list[PredictTaskResultDTO]] = None

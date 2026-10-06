from dataclasses import dataclass
from typing import Optional, Annotated

import msgspec

from pimfp.entity import PredictionType, UltrasoundType, PigType

_MAX_ROWS = 10000

Feature = Annotated[
    float, msgspec.Meta(
        ge=0,
        le=100
    )
]


@dataclass
class BackfatSummaryDTO(msgspec.Struct, rename="camel"):
    row_idx: Annotated[int, msgspec.Meta(ge=0, lt=_MAX_ROWS)]
    name: Annotated[str, msgspec.Meta(min_length=1)]
    image: Annotated[str, msgspec.Meta(min_length=1)]
    feature1: Optional[Feature]
    feature2: Optional[Feature]


@dataclass
class LoinEyeSummaryDTO(msgspec.Struct, rename="camel"):
    row_idx: Annotated[int, msgspec.Meta(ge=0, lt=_MAX_ROWS)]
    name: Annotated[str, msgspec.Meta(min_length=1)]
    image: Annotated[str, msgspec.Meta(min_length=1)]
    feature: Optional[Feature]


@dataclass
class DoubleViewSummaryDTO(msgspec.Struct, rename="camel"):
    row_idx: Annotated[int, msgspec.Meta(ge=0, lt=_MAX_ROWS)]
    name: Annotated[str, msgspec.Meta(min_length=1)]
    backfat: Annotated[str, msgspec.Meta(min_length=1)]
    loin_eye: Annotated[str, msgspec.Meta(min_length=1)]
    feature1: Optional[Feature]
    feature2: Optional[Feature]
    feature3: Optional[Feature]


@dataclass
class PredictionReqBase(msgspec.Struct, rename="camel", tag_field="predictionType"):
    ultrasound_type: UltrasoundType
    pig_type: PigType


@dataclass
class BackfatReq(PredictionReqBase, rename="camel", tag=PredictionType.BACKFAT.value):
    summary_list: Annotated[list[BackfatSummaryDTO], msgspec.Meta(min_length=1, max_length=_MAX_ROWS)]


@dataclass
class LoinEyeReq(PredictionReqBase, rename="camel", tag=PredictionType.LOIN_EYE.value):
    summary_list: Annotated[list[LoinEyeSummaryDTO], msgspec.Meta(min_length=1, max_length=_MAX_ROWS)]


@dataclass
class DoubleViewReq(PredictionReqBase, rename="camel", tag=PredictionType.BACKFAT_LOIN_EYE.value):
    summary_list: Annotated[list[DoubleViewSummaryDTO], msgspec.Meta(min_length=1, max_length=_MAX_ROWS)]


@dataclass
class PREDICTION000Rsp(msgspec.Struct, rename="camel"):
    flow_no: str

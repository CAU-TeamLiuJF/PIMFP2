from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import NamedTuple, Optional

from .common import SupportedLocaleEnum


class PredictTaskStatus(IntEnum):
    INITIAL = 0
    PREPARED = 1
    QUEUEING = 2
    PROCESSING = 3
    ACCOMPLISHED = 4
    FAILED = 5
    REJECTED = 6


class PredictionType(IntEnum):
    BACKFAT = 0
    LOIN_EYE = 1
    BACKFAT_LOIN_EYE = 2


class UltrasoundType(IntEnum):
    EXPRO = 0
    UNICORN_VET = 1
    BOXERLY = 2
    KAIXIN = 3
    WELLD = 4
    # ANOTHER_ULTRASOUND = 2
    # OTHER_ULTRASOUND = 3
    # ...


class PigType(IntEnum):
    LEAN = 0
    FAT = 1


@dataclass
class DoubleViewSummary:
    row_idx: int
    name: str
    backfat: str
    loin_eye: str
    feature1: Optional[float]
    feature2: Optional[float]
    feature3: Optional[float]


@dataclass
class BackfatSummary:
    row_idx: int
    name: str
    image: str
    feature1: Optional[float]
    feature2: Optional[float]


@dataclass
class LoinEyeSummary:
    row_idx: int
    name: str
    image: str
    feature: Optional[float]


@dataclass
class PredictTask:
    prediction_type: PredictionType
    ultrasound_type: UltrasoundType
    pig_type: PigType


@dataclass
class BackfatTask(PredictTask):
    summary_list: list[BackfatSummary]


@dataclass
class LoinEyeTask(PredictTask):
    summary_list: list[LoinEyeSummary]


@dataclass
class DoubleViewTask(PredictTask):
    summary_list: list[DoubleViewSummary]


@dataclass
class QueuePredictionTask:
    flow_no: str
    email: str
    submit_at: datetime
    locale: SupportedLocaleEnum
    images_mapping: dict[str, str]
    prediction_type: PredictionType
    ultrasound_type: UltrasoundType
    pig_type: PigType


@dataclass
class QueueBackfatTask(QueuePredictionTask):
    summary_list: list[BackfatSummary]


@dataclass
class QueueLoinEyeTask(QueuePredictionTask):
    summary_list: list[LoinEyeSummary]


@dataclass
class QueueDoubleViewTask(QueuePredictionTask):
    summary_list: list[DoubleViewSummary]


class CropBox(NamedTuple):
    top: int
    bottom: int
    left: int
    right: int


IMAGE_SIZE: dict[UltrasoundType, dict[PredictionType, dict[tuple[int, int], CropBox]]] = {
    UltrasoundType.EXPRO: {
        PredictionType.BACKFAT: {
            (1079, 680): CropBox(50, 650, 200, 800),  # 600*600
            (1138, 854): CropBox(50, 650, 200, 800),  # 600*600
            (1215, 765): CropBox(50, 650, 200, 800),  # 600*600
            (1998, 1499): CropBox(0, 1200, 400, 1600),  # 1200*1200
            (580, 480): CropBox(80, 400, 70, 390),  # 320*320
            (613, 526): CropBox(45, 405, 150, 510),  # 360*360
            (1351, 960): CropBox(45, 845, 250, 1050),  # 800*800
            (730, 660): CropBox(80, 580, 60, 560),  # 500*500, fuzhiyuan
            (640, 480): CropBox(50, 410, 40, 400),  #360*360, fuzhiyuan
        },
        PredictionType.LOIN_EYE: {
            (1215, 765): CropBox(45, 650, 765, 990),  # 720*720 上下左右
        },
    },
    UltrasoundType.UNICORN_VET: {
        PredictionType.BACKFAT: {
            (940, 720): CropBox(60, 560, 150, 650),  # 500*500
            (880, 688): CropBox(180, 580, 250, 650),  # 400*400
            (708, 698): CropBox(130, 580, 130, 580),  # 450*450
            (1525, 1030): CropBox(100, 980, 275, 1155),  # 880*880
            (1220, 794): CropBox(70, 750, 220, 900),  # 680*680
        },
        PredictionType.LOIN_EYE: {
            (940, 720): CropBox(60, 720, 120, 780),  # 660*660
            (1525, 1030): CropBox(100, 980, 275, 1155),  # 880*880
        }
    },
    UltrasoundType.BOXERLY: {
        PredictionType.BACKFAT: {
            (1936, 1440): CropBox(160, 1320, 250, 1410),  # 1160*1600
            (1898, 1443): CropBox(120, 1170, 250, 1300),  # 1050*1050
        },
        PredictionType.LOIN_EYE: {
            (1936, 1440): CropBox(120, 1380, 250, 1510),  # 1260*1260上下左右
            (1898, 1443): CropBox(120, 1220, 250, 1350),  # 1100*1100
            (1898, 1426): CropBox(120, 1220, 250, 1350),  # 1100*1100
        }
    },
    UltrasoundType.KAIXIN: {
        PredictionType.BACKFAT: {
            (640, 480): CropBox(50, 470, 60, 480),  # 420*420
        },
        PredictionType.LOIN_EYE: {
            (640, 480): CropBox(50, 480, 70, 500),  # 430*430上下左右
        }
    },
    UltrasoundType.WELLD: {
        PredictionType.BACKFAT: {
            (871, 600): CropBox(90, 570, 30, 510),  # 480*480
        },
        PredictionType.LOIN_EYE: {
            (871, 600): CropBox(90, 570, 30, 510),  # 480*480
        }
    },
    # UltrasoundType.ANOTHER_ULTRASOUND: {
    #     PredictionType.BACKFAT: {
    #         (1079, 680): CropBox(50, 650, 200, 800),  # 600*600
    #         (1138, 854): CropBox(50, 650, 200, 800),  # 600*600
    #     },
    #     PredictionType.LOIN_EYE: {
    #         (1215, 765): CropBox(45, 650, 765, 990),  # 720*720 上下左右
    #     },
    # },
    # ...
}

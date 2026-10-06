from datetime import datetime, timezone, date
from typing import Optional, Any

from peewee import fn

from pimfp.entity import PredictTaskStatus, PredictionType, UltrasoundType, PigType
from pimfp.model import PredictTask, DailyQuota, ImageMapping


def get_quota(email: str, today: date) -> Optional[DailyQuota]:
    return DailyQuota.get_or_none(DailyQuota.email == email, DailyQuota.quota_date == today)


def get_quota_or_create(email: str, today: date) -> tuple[DailyQuota, bool]:
    return DailyQuota.get_or_create(email=email, quota_date=today)


def incr_quota(email: str, today: date, increment: int, limit: int) -> bool:
    rows = DailyQuota.update(
        used_quota=DailyQuota.used_quota + increment
    ).where(
        (DailyQuota.email == email) &
        (DailyQuota.quota_date == today) &
        (DailyQuota.used_quota + increment <= limit)
    ).execute()
    return rows > 0


def dec_quota(email: str, today: date, decrement: int) -> bool:
    """
    UPDATE `daily_quota` SET `used_quota` = `used_quota` - ${decrement}
    WHERE `email` = ${email} AND `quota_date` = ${date}
    """
    datetime.now(timezone.utc).date()
    rows = DailyQuota.update(
        used_quota=fn.GREATEST(0, DailyQuota.used_quota - decrement)
    ).where(
        (DailyQuota.email == email) &
        (DailyQuota.quota_date == today)
    ).execute()
    return rows > 0


def insert_predict_task(flow_no: str, email: str, prediction_type: PredictionType, ultrasound_type: UltrasoundType,
                        pig_type: PigType, summary: str, total_images: int, submit_at: datetime) -> bool:
    """
    INSERT INTO `predict_task` (`flow_no`, `email`, `prediction_type`, `ultrasound_type`, `pig_type`, `summary`, `submit_at`)
    VALUES (${flow_no}, ${upload_id}, ${email}, ${prediction_type}, ${ultrasound_type}, ${pig_type}, ${summary}, ${utcnow})
    """
    rows = PredictTask.insert(
        flow_no=flow_no,
        email=email,
        prediction_type=prediction_type,
        ultrasound_type=ultrasound_type,
        pig_type=pig_type,
        summary=summary,
        total_images=total_images,
        submit_at=submit_at
    ).execute()
    return rows > 0


def get_predict_task(flow_no: str) -> Optional[PredictTask]:
    """
    SELECT * FROM `predict_task` WHERE `flow_no` = ${flow_no}
    """
    return PredictTask.get_or_none(PredictTask.flow_no == flow_no)


def reject_predict_task(flow_no: str, reason: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = ${PredictTaskStatus.REJECTED}, `reason` = ${reason}
    WHERE `flow_no` = ${flow_no}
    AND `status` NOT IN (${PredictTaskStatus.REJECTED}, ${PredictTaskStatus.FAILED}, ${PredictTaskStatus.ACCOMPLISHED})
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.REJECTED,
        reason=reason,
        completed_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        ~(PredictTask.status << [PredictTaskStatus.REJECTED, PredictTaskStatus.FAILED, PredictTaskStatus.ACCOMPLISHED])
    ).execute()
    return rows > 0


def try_reject_predict_task(flow_no: str, status: PredictTaskStatus, reason: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = PredictTaskStatus.REJECTED, `reason` = ${reason}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${status}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.REJECTED,
        reason=reason,
        completed_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == status)
    ).execute()
    return rows > 0


def uploading_images(flow_no: str, num: int) -> bool:
    """
    UPDATE `predict_task` SET `uploading_images` = `uploading_images` + `num`
    WHERE `flow_no` = ${flow_no}
    AND `status` == ${PredictTaskStatus.INITIAL}
    AND `uploading_images` + ${num} <= `total_images`
    """
    rows = PredictTask.update(
        uploading_images=PredictTask.uploading_images + num
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == PredictTaskStatus.INITIAL) &
        (PredictTask.uploading_images + num <= PredictTask.total_images)
    ).execute()
    return rows > 0


def try_fail_predict_task(flow_no: str, status: PredictTaskStatus, reason: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = PredictTaskStatus.FAILED, `reason` = ${reason}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${status}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.FAILED,
        reason=reason,
        completed_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == status)
    ).execute()
    return rows > 0


def fail_predict_task(flow_no: str, reason: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = ${PredictTaskStatus.FAILED}, `reason` = ${reason}
    WHERE `flow_no` = ${flow_no}
    AND `status` NOT IN (${PredictTaskStatus.REJECTED}, ${PredictTaskStatus.FAILED}, ${PredictTaskStatus.ACCOMPLISHED})
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.FAILED,
        reason=reason,
        completed_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        ~(PredictTask.status << [PredictTaskStatus.REJECTED, PredictTaskStatus.FAILED, PredictTaskStatus.ACCOMPLISHED])
    ).execute()
    return rows > 0


def insert_many_image_mapping(images_mapping) -> None:
    ImageMapping.insert_many(images_mapping).execute()


def select_predict_task_for_update(flow_no: str) -> Optional[PredictTask]:
    """
    SELECT * FROM `predict_task` WHERE `flow_no` = ${flow_no} FOR UPDATE
    """
    return PredictTask.select().where(PredictTask.flow_no == flow_no).for_update().first()


def update_uploaded_images(flow_no: str, num: int) -> bool:
    """
    UPDATE `predict_task`
    SET `status` = ${status}, `uploaded_images`=${num}
    WHERE `flow_no` = ${flow_no}
    """
    rows = PredictTask.update(uploaded_images=num).where(PredictTask.flow_no == flow_no).execute()
    return rows > 0


def prepared_predict_task(flow_no: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = ${PredictTaskStatus.PREPARED}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${PredictTaskStatus.INITIAL}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.PREPARED,
        prepared_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == PredictTaskStatus.INITIAL)
    ).execute()
    return rows > 0


def queueing_predict_task(flow_no: str) -> bool:
    """
    UPDATE `predict_task` SET `status` = ${PredictTaskStatus.QUEUEING}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${PredictTaskStatus.PREPARED}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.QUEUEING,
        queue_at=datetime.now(timezone.utc),
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == PredictTaskStatus.PREPARED)
    ).execute()
    return rows > 0


def query_images_mapping(flow_no: str) -> dict[str, str]:
    """
    SELECT `filename`, `local_path` FROM `image_mapping` WHERE `flow_no` = ${flow_no}
    """
    return dict(
        ImageMapping
        .select(ImageMapping.filename, ImageMapping.local_path)
        .where(ImageMapping.flow_no == flow_no)
        .tuples()
    )


def processing_predict_task(flow_no: str):
    """
    UPDATE `predict_task`
    SET `status` = ${PredictTaskStatus.PROCESSING}, `processing_at` = ${utcnow}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${PredictTaskStatus.QUEUEING}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.PROCESSING,
        processing_at=datetime.now(timezone.utc)
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == PredictTaskStatus.QUEUEING)
    ).execute()
    return rows > 0


def accomplish_predict_task(flow_no: str, result: str) -> bool:
    """
    UPDATE `predict_task`
    SET `status` = ${PredictTaskStatus.ACCOMPLISHED}, `completed_at` = ${utcnow}, `result` = ${result}
    WHERE `flow_no` = ${flow_no}
    AND `status` = ${PredictTaskStatus.PROCESSING}
    """
    rows = PredictTask.update(
        status=PredictTaskStatus.ACCOMPLISHED,
        completed_at=datetime.now(timezone.utc),
        result=result
    ).where(
        (PredictTask.flow_no == flow_no) &
        (PredictTask.status == PredictTaskStatus.PROCESSING)
    ).execute()
    return rows > 0


def get_total_predicted_images() -> int:
    """
    SELECT SUM(`total_images`)
    FROM `predict_task`
    WHERE `status` = ${PredictTaskStatus.ACCOMPLISHED}
    """
    result = PredictTask.select(
        fn.SUM(PredictTask.total_images)
    ).where(
        PredictTask.status == PredictTaskStatus.ACCOMPLISHED
    ).scalar()
    return int(result or 0)


def get_predict_task_total(email: str, status: PredictTaskStatus) -> int:
    """
    SELECT COUNT(`id`)
    FROM `predict_task`
    WHERE `email` = ${email}
    AND `status` = ${status}
    """
    query = PredictTask.select(fn.COUNT(PredictTask.id)).where(PredictTask.email == email)
    if status is not None:
        query = query.where(PredictTask.status == status)
    return int(query.scalar() or 0)


def query_predict_task_list(email: str, status: PredictTaskStatus, page_no: int, page_size: int) -> Optional[list[PredictTask]]:
    """
    SELECT *
    FROM `predict_task`
    WHERE `email` = ${email}
    AND `status` = ${status}
    ORDER BY `flow_no` DESC
    LIMIT ${page_size} OFFSET ${(page_no - 1) * page_size}
    """
    query = PredictTask.select().where(PredictTask.email == email)
    if status is not None:
        query = query.where(PredictTask.status == status)
    query = query.order_by(PredictTask.flow_no.desc()).limit(page_size).offset((page_no - 1) * page_size)
    return list(query)


def clear_images_mapping(flow_no: str) -> int:
    """
    DELETE FROM `image_mapping` WHERE `flow_no` = ${flow_no}
    """
    return ImageMapping.delete().where(ImageMapping.flow_no == flow_no).execute()

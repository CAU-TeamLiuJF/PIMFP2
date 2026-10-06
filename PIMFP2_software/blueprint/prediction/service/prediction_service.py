import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Union, Optional

import msgspec
import shortuuid
from PIL import Image
from flask import g
from peewee import chunked, IntegrityError
from playhouse.shortcuts import model_to_dict
from werkzeug.datastructures import FileStorage

from pimfp import logger
from pimfp.config import config
from pimfp.dao import auth_dao, prediction_dao
from pimfp.entity import RoleEnum, BackfatTask, LoinEyeTask, DoubleViewTask, PredictionType, PredictTaskStatus, IMAGE_SIZE, \
    BackfatSummary, LoinEyeSummary, DoubleViewSummary, QueueBackfatTask, QueueLoinEyeTask, QueueDoubleViewTask
from pimfp.error import BizI18nError, BizError, PredictionErrCode
from pimfp.middleware.db import db
from pimfp.middleware.redis import Region, redis
from pimfp.model import PredictTask, ImageMapping
from pimfp.service import model

_LOGGER = logger.get_logger(__name__)

ABNORMAL_PREDICT_TASK_STATUS = "abnormal predict task status"
TOO_MANY_IMAGES = "too many images"
UNKNOWN_IMAGES = "unknown image"
DUPLICATE_IMAGES = "duplicate image"
INVALID_IMAGE_SIZE = "invalid image size"
ERROR_WHEN_INCR_UPLOADING = "error when incr uploading"
ERROR_WHEN_SAVING_IMAGES = "error when saving images"
ERROR_WHEN_SAVING_IMAGES_MAPPING = "error when saving images mapping"
ERROR_WHEN_INCR_UPLOADED = "error when incr uploaded"
ERROR_WHEN_PREPARED_TO_QUEUEING = "error when PREPARED to QUEUEING"
ERROR_WHEN_SUBMITTING_TASK = "error when submitting task to queue"
REJECTED_BY_TASK_QUEUE = "rejected by task queue"


def upload_active_key(flow_no: str):
    return f"{Region.UPLOAD.region}::{flow_no}"


def apply_predict(predict_task: Union[BackfatTask, LoinEyeTask, DoubleViewTask]) -> str:
    try:
        return _apply_predict(predict_task)
    except BizI18nError:
        raise
    except BizError:
        raise
    except Exception as e:
        _LOGGER.error("error occurs when apply predict task", exc_info=e)
        raise BizI18nError(PredictionErrCode.APPLY_PREDICT_TASK_FAILED)


def _apply_predict(predict_task: Union[BackfatTask, LoinEyeTask, DoubleViewTask]) -> str:
    valid, require_images = _check_task_summary(predict_task)
    if not valid:
        raise BizI18nError(PredictionErrCode.APPLY_PREDICT_TASK_FAILED)

    is_vip = auth_dao.has_role(g.user.email, RoleEnum.VIP.code)
    if is_vip:
        return _vip_apply_predict(predict_task, require_images)
    return _basic_apply_predict(predict_task, require_images)


def _vip_apply_predict(predict_task: Union[BackfatTask, LoinEyeTask, DoubleViewTask], require_images: set[str]) -> str:
    max_image_count = config.app.get("vip_max_image_count", 500)
    if len(require_images) > max_image_count:
        raise BizI18nError(PredictionErrCode.PREDICT_VIP_TOO_MANY_IMAGES)

    flow_no = _generate_flow_no()
    key = upload_active_key(flow_no)
    try:
        with db.atomic():
            prediction_dao.insert_predict_task(
                flow_no=flow_no,
                email=g.user.email,
                prediction_type=predict_task.prediction_type,
                ultrasound_type=predict_task.ultrasound_type,
                pig_type=predict_task.pig_type,
                summary=msgspec.json.encode(predict_task.summary_list).decode('utf-8'),
                total_images=len(require_images),
                submit_at=datetime.now(timezone.utc)
            )
            redis.set(key, 1, ex=Region.UPLOAD.ttl)
            return flow_no
    except Exception as e:
        _LOGGER.error(f"failed to create predict task:{flow_no}", exc_info=e)
        redis.delete(key)
        raise BizI18nError(PredictionErrCode.APPLY_PREDICT_TASK_FAILED)


def _basic_apply_predict(predict_task: Union[BackfatTask, LoinEyeTask, DoubleViewTask], require_images: set[str]):
    submit_at = datetime.now(timezone.utc)
    today = submit_at.date()
    limit = config.app.get("basic_max_image_count", 100)
    quota, _ = prediction_dao.get_quota_or_create(g.user.email, today)
    if quota.used_quota + len(require_images) > limit:
        raise BizError(PredictionErrCode.PREDICT_BASIC_TOO_MANY_IMAGES, {"used_quota": quota.used_quota})

    flow_no = _generate_flow_no()
    key = upload_active_key(flow_no)
    try:
        with db.atomic():
            result = prediction_dao.incr_quota(g.user.email, today, len(require_images), limit)
            if not result:
                quota = prediction_dao.get_quota(g.user.email, today)
                raise BizError(PredictionErrCode.PREDICT_BASIC_TOO_MANY_IMAGES, {"used_quota": quota.used_quota})
            prediction_dao.insert_predict_task(
                flow_no=flow_no,
                email=g.user.email,
                prediction_type=predict_task.prediction_type,
                ultrasound_type=predict_task.ultrasound_type,
                pig_type=predict_task.pig_type,
                summary=msgspec.json.encode(predict_task.summary_list).decode('utf-8'),
                total_images=len(require_images),
                submit_at=submit_at
            )
            redis.set(key, 1, ex=Region.UPLOAD.ttl)
            return flow_no
    except Exception as e:
        _LOGGER.error(f"failed to create predict task:{flow_no}", exc_info=e)
        redis.delete(key)
        if isinstance(e, BizError):
            raise e
        raise BizI18nError(PredictionErrCode.APPLY_PREDICT_TASK_FAILED)


def _check_task_summary(predict_task: Union[BackfatTask, LoinEyeTask, DoubleViewTask]) -> tuple[bool, Optional[set]]:
    if predict_task.prediction_type in (PredictionType.BACKFAT, PredictionType.LOIN_EYE):
        return _check_single_view_summary(predict_task)
    elif predict_task.prediction_type == PredictionType.BACKFAT_LOIN_EYE:
        return _check_double_view_summary(predict_task)
    return False, None


def _check_single_view_summary(predict_task: Union[BackfatTask, LoinEyeTask]) -> tuple[bool, Optional[set]]:
    summary_list = predict_task.summary_list
    name_image_set = set()
    image_set = set()
    for summary in summary_list:
        name_image = f"{summary.name}_{summary.image}"
        if name_image in name_image_set:
            return False, None  # duplicate rows
        name_image_set.add(name_image)

        if summary.image in image_set:
            return False, None  # image used in different pigs
        image_set.add(summary.image)
    return True, image_set


def _check_double_view_summary(predict_task: DoubleViewTask) -> tuple[bool, Optional[set]]:
    summary_list = predict_task.summary_list
    name_image_set = set()
    backfat_set = set()
    loin_eye_set = set()
    image_name_dict = dict()

    for summary in summary_list:
        name_image = f"{summary.name}_{summary.backfat}_{summary.loin_eye}"
        if name_image in name_image_set:
            return False, None  # duplicate rows
        name_image_set.add(name_image)

        prev_name = image_name_dict.get(summary.backfat)
        if prev_name and prev_name != summary.name:
            return False, None  # image used in different pigs
        prev_name = image_name_dict.get(summary.loin_eye)
        if prev_name and prev_name != summary.name:
            return False, None  # image used in different pigs
        image_name_dict[summary.backfat] = summary.name
        image_name_dict[summary.loin_eye] = summary.name

        if summary.backfat in loin_eye_set:
            return False, None  # image used both in backfat and loin eye
        backfat_set.add(summary.backfat)
        if summary.loin_eye in backfat_set:
            return False, None  # image used both in backfat and loin eye
        loin_eye_set.add(summary.loin_eye)
    return True, backfat_set.union(loin_eye_set)


def _generate_flow_no() -> str:
    now = datetime.now(timezone.utc)
    key = f"{Region.FLOWNO.region}::{now.strftime('%Y%m%d')}"
    seq = redis.incr(key, 1)
    if seq == 1:
        redis.expire(key, Region.FLOWNO.ttl)
    return f"PIMFP{now.strftime('%Y%m%d%H%M%S')}N{str(seq).zfill(6)[-6:]}"  # PIMFP20260229215312N000001


def upload_images(flow_no: str, images: list[FileStorage]):
    try:
        _upload_images(flow_no, images)
    except BizI18nError:
        raise
    except BizError:
        raise
    except Exception as e:
        _LOGGER.error(f"error occurs when upload images:{flow_no}", exc_info=e)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)


def _upload_images(flow_no: str, images: list[FileStorage]):
    predict_task = prediction_dao.get_predict_task(flow_no)
    if not predict_task:
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

    if predict_task.status != PredictTaskStatus.INITIAL:
        _reject_predict_task(flow_no, ABNORMAL_PREDICT_TASK_STATUS)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

    if len(images) + predict_task.uploaded_images > predict_task.total_images:
        _reject_predict_task(flow_no, TOO_MANY_IMAGES)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

    # check images
    _check_uploading_images(predict_task, images)

    # increase uploading images
    _incr_uploading_images(predict_task, len(images))

    # save images
    images_path = _save_images(predict_task, images)

    # save images mapping
    _save_images_mapping(predict_task, images_path)

    # increase uploaded images
    _incr_uploaded_images(predict_task, len(images))


def _check_uploading_images(predict_task: PredictTask, images: list[FileStorage]):
    required_images = _get_require_images(predict_task)
    images_set = set()
    for image in images:
        if not image.filename or not image.filename in required_images:
            _LOGGER.error(f"unknown image:{image.filename}")
            _reject_predict_task(predict_task.flow_no, UNKNOWN_IMAGES)
            raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

        if image.filename in images_set:
            _reject_predict_task(predict_task.flow_no, DUPLICATE_IMAGES)
            raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)
        images_set.add(image.filename)

        with Image.open(image.stream) as img:
            prediction_type = required_images[image.filename]
            whsize = IMAGE_SIZE[predict_task.ultrasound_type][prediction_type]
            w, h = img.size
            if (w, h) not in whsize:
                _LOGGER.error(f"invalid image size:{image.filename}:w:{w}:h:{h}")
                _reject_predict_task(predict_task.flow_no, INVALID_IMAGE_SIZE)
                raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)
        image.seek(0, os.SEEK_SET)


def _get_require_images(predict_task: PredictTask) -> dict[str, PredictionType]:
    if predict_task.prediction_type is PredictionType.BACKFAT:
        summary_list = msgspec.json.decode(predict_task.summary, type=list[BackfatSummary])
        require_images = {summary.image: PredictionType.BACKFAT for summary in summary_list if summary.image}
    elif predict_task.prediction_type is PredictionType.LOIN_EYE:
        summary_list = msgspec.json.decode(predict_task.summary, type=list[LoinEyeSummary])
        require_images = {summary.image: PredictionType.LOIN_EYE for summary in summary_list if summary.image}
    else:  # PredictionType.BACKFAT_LOIN_EYE
        summary_list = msgspec.json.decode(predict_task.summary, type=list[DoubleViewSummary])
        loin_dict = {summary.loin_eye: PredictionType.LOIN_EYE for summary in summary_list if summary.loin_eye}
        backfat_dict = {summary.backfat: PredictionType.BACKFAT for summary in summary_list if summary.backfat}
        require_images = {**loin_dict, **backfat_dict}
    return require_images


def _reject_predict_task(flow_no: str, reason):
    try:
        result = prediction_dao.reject_predict_task(flow_no, reason)
    except Exception as e:
        _LOGGER.warning("error occurs when rejecting predict task", exc_info=e)
        return

    if result:
        _remove_local(Path(config.app.storage_dir) / flow_no)


def _fail_predict_task(flow_no: str, reason: str):
    try:
        result = prediction_dao.fail_predict_task(flow_no, reason)
    except Exception as e:
        _LOGGER.warning("error occurs when failing predict task", exc_info=e)
        return

    if result:
        _remove_local(Path(config.app.storage_dir) / flow_no)


def _incr_uploading_images(predict_task: PredictTask, num: int):
    flow_no = predict_task.flow_no
    try:
        result = prediction_dao.uploading_images(flow_no, num)
    except Exception as e:
        _LOGGER.error(f"error occurred when increasing uploading images:{flow_no}", exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.INITIAL, ERROR_WHEN_INCR_UPLOADING)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

    if not result:
        _reject_predict_task(flow_no, TOO_MANY_IMAGES)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)


def _try_fail_restore_quota(predict_task: PredictTask, status: PredictTaskStatus, reason: str):
    is_vip = auth_dao.has_role(predict_task.email, RoleEnum.VIP.code)
    if is_vip:
        _fail_predict_task(predict_task.flow_no, reason)
        return

    failed = _try_fail_predict_task(predict_task.flow_no, status, reason)
    if failed:
        _restore_quota(predict_task)
    else:
        _fail_predict_task(predict_task.flow_no, reason)


def _try_fail_predict_task(flow_no: str, status: PredictTaskStatus, reason: str) -> bool:
    try:
        result = prediction_dao.try_fail_predict_task(flow_no, status, reason)
    except Exception as e:
        _LOGGER.warning(f"error occurs when failing predict task from {status} to FAILED", exc_info=e)
        return False
    if result:
        _remove_local(Path(config.app.storage_dir) / flow_no)
    return result


def _save_images(predict_task: PredictTask, images: list[FileStorage]) -> dict[str, str]:
    images_path = dict()
    try:
        storage_dir = Path(config.app.storage_dir) / predict_task.flow_no
        storage_dir.mkdir(parents=True, exist_ok=True)
        for image in images:
            safe_file_name = shortuuid.uuid()
            local_path = storage_dir / safe_file_name
            image.save(local_path)
            images_path[image.filename] = local_path
    except Exception as e:
        _LOGGER.error("error occurs when saving images", exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.INITIAL, ERROR_WHEN_SAVING_IMAGES)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

    return images_path


def _save_images_mapping(predict_task: PredictTask, images_path: dict[str, str]):
    data_to_insert = [
        {
            ImageMapping.flow_no: predict_task.flow_no,
            ImageMapping.filename: original_name,
            ImageMapping.local_path: local_path,
        }
        for original_name, local_path in images_path.items()
    ]

    try:
        with db.atomic():
            for batch in chunked(data_to_insert, 100):
                prediction_dao.insert_many_image_mapping(batch)
    except IntegrityError as e:
        _LOGGER.error(f"duplicate images detected", exc_info=e)
        _reject_predict_task(predict_task.flow_no, DUPLICATE_IMAGES)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)
    except Exception as e:
        _LOGGER.error(f"error occurs when saving images mapping", exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.INITIAL, ERROR_WHEN_SAVING_IMAGES_MAPPING)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)


def _incr_uploaded_images(predict_task: PredictTask, num: int):
    reject_reason = None
    try:
        with db.atomic():
            locked_task = prediction_dao.select_predict_task_for_update(predict_task.flow_no)

            if locked_task.status != PredictTaskStatus.INITIAL:
                reject_reason = ABNORMAL_PREDICT_TASK_STATUS
                raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

            total_uploaded = locked_task.uploaded_images + num
            if total_uploaded > locked_task.total_images:
                reject_reason = TOO_MANY_IMAGES
                raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)

            if reject_reason is None:
                prediction_dao.update_uploaded_images(locked_task.flow_no, total_uploaded)
                if total_uploaded == locked_task.total_images:
                    prediction_dao.prepared_predict_task(locked_task.flow_no)
    except BizI18nError as e:
        _LOGGER.warning(f"failed to increase uploaded images due to {reject_reason}", exc_info=e)
        _reject_predict_task(predict_task.flow_no, reject_reason)
        raise
    except Exception as e:
        _LOGGER.error(f"error occurs when increasing uploaded images", exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.INITIAL, ERROR_WHEN_INCR_UPLOADED)
        raise BizI18nError(PredictionErrCode.UPLOAD_IMAGES_FAILED)


def _remove_local(local_path: Path):
    _LOGGER.info(f"try to clear local file:{local_path}")
    try:
        if local_path.exists():
            if local_path.is_dir():
                shutil.rmtree(local_path)
            else:
                os.remove(local_path)
    except Exception as e:
        _LOGGER.warning(f"failed to remove local file:{local_path}", exc_info=e)


def predict(flow_no: str):
    predict_task = prediction_dao.get_predict_task(flow_no)
    if not predict_task:
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)

    if predict_task.status != PredictTaskStatus.PREPARED:
        _reject_predict_task(flow_no, ABNORMAL_PREDICT_TASK_STATUS)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)

    # PREPARED -> QUEUEING
    _queueing_predict_task(predict_task)

    # submit
    _submit_predict_task(predict_task)


def _queueing_predict_task(predict_task: PredictTask):
    try:
        result = prediction_dao.queueing_predict_task(predict_task.flow_no)
    except Exception as e:
        _LOGGER.error(f"error occurs when changing predict task:{predict_task.flow_no} from PREPARED to QUEUEING",
                      exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.PREPARED, ERROR_WHEN_PREPARED_TO_QUEUEING)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)

    if not result:
        _LOGGER.error(f"failed to change predict task:{predict_task.flow_no} from PREPARED to QUEUEING")
        _reject_predict_task(predict_task.flow_no, ABNORMAL_PREDICT_TASK_STATUS)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)


def _submit_predict_task(predict_task: PredictTask):
    try:
        images_mapping = prediction_dao.query_images_mapping(predict_task.flow_no)
        if predict_task.prediction_type is PredictionType.BACKFAT:
            summary_list = msgspec.json.decode(predict_task.summary, type=list[BackfatSummary])
            queue_task = QueueBackfatTask(
                prediction_type=PredictionType.BACKFAT,
                email=predict_task.email,
                flow_no=predict_task.flow_no,
                submit_at=predict_task.submit_at,
                locale=g.locale,
                ultrasound_type=predict_task.ultrasound_type,
                pig_type=predict_task.pig_type,
                summary_list=summary_list,
                images_mapping=images_mapping,
            )

        elif predict_task.prediction_type is PredictionType.LOIN_EYE:
            summary_list = msgspec.json.decode(predict_task.summary, type=list[LoinEyeSummary])
            queue_task = QueueLoinEyeTask(
                prediction_type=PredictionType.LOIN_EYE,
                email=predict_task.email,
                flow_no=predict_task.flow_no,
                submit_at=predict_task.submit_at,
                locale=g.locale,
                ultrasound_type=predict_task.ultrasound_type,
                pig_type=predict_task.pig_type,
                summary_list=summary_list,
                images_mapping=images_mapping,
            )
        else:
            summary_list = msgspec.json.decode(predict_task.summary, type=list[DoubleViewSummary])
            queue_task = QueueDoubleViewTask(
                prediction_type=PredictionType.BACKFAT_LOIN_EYE,
                email=predict_task.email,
                flow_no=predict_task.flow_no,
                submit_at=predict_task.submit_at,
                locale=g.locale,
                ultrasound_type=predict_task.ultrasound_type,
                pig_type=predict_task.pig_type,
                summary_list=summary_list,
                images_mapping=images_mapping,
            )

        is_vip = auth_dao.has_role(predict_task.email, RoleEnum.VIP.code)
        if is_vip:
            queued_result = model.vip_submit(queue_task)
        else:
            queued_result = model.basic_submit(queue_task)
    except Exception as e:
        _LOGGER.error(f"error occurs when submitting predict task:{predict_task.flow_no}", exc_info=e)
        _try_fail_restore_quota(predict_task, PredictTaskStatus.QUEUEING, ERROR_WHEN_SUBMITTING_TASK)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)

    if not queued_result:
        _LOGGER.error(f"failed to submit predict task:{predict_task.flow_no}")
        if is_vip:
            _reject_predict_task(predict_task.flow_no, REJECTED_BY_TASK_QUEUE)
        else:
            rejected = _try_reject_predict_task(predict_task.flow_no, PredictTaskStatus.QUEUEING, REJECTED_BY_TASK_QUEUE)
            if rejected:
                _restore_quota(predict_task)
            else:
                _reject_predict_task(predict_task.flow_no, REJECTED_BY_TASK_QUEUE)
        raise BizI18nError(PredictionErrCode.PREDICT_FAILED)


def _try_reject_predict_task(flow_no: str, status: PredictTaskStatus, reason: str) -> bool:
    try:
        result = prediction_dao.try_reject_predict_task(flow_no, status, reason)
    except Exception as e:
        _LOGGER.warning(f"error occurs when failing predict task from {status} to REJECTED", exc_info=e)
        return False
    if result:
        _remove_local(Path(config.app.storage_dir) / flow_no)
    return result


def _restore_quota(predict_task: PredictTask):
    try:
        prediction_dao.dec_quota(predict_task.email, predict_task.submit_at.date(), predict_task.total_images)
    except Exception as e:
        _LOGGER.warning(f"error occurs when restoring quota", exc_info=e)


def get_latest_avail_quota() -> int:
    is_vip = auth_dao.has_role(g.user.email, RoleEnum.VIP.code)
    if is_vip:
        raise BizI18nError(PredictionErrCode.VIP_INFINITE_QUOTA)
    today = datetime.now(timezone.utc).date()
    quota, _ = prediction_dao.get_quota_or_create(g.user.email, today)
    return max(config.app.get("basic_max_image_count", 100) - quota.used_quota, 0)


def get_total_predicted_images() -> int:
    total = redis.get(f"{Region.DAILY_STATS.region}::predicted_images", type=int)
    if total is None:
        total = prediction_dao.get_total_predicted_images()
        redis.set(f"{Region.DAILY_STATS.region}::predicted_images", total, nx=True, ex=Region.DAILY_STATS.ttl)
    return total


def predict_task_list(page_no: int, page_size: int, status: PredictTaskStatus) -> tuple[list[dict], int]:
    total = prediction_dao.get_predict_task_total(g.user.email, status)
    predict_list = prediction_dao.query_predict_task_list(g.user.email, status, page_no, page_size) or []

    return [{
        "flow_no": predict_task.flow_no,
        "submit_at": predict_task.submit_at.strftime("%Y-%m-%d %H:%M:%S UTC") if predict_task.submit_at else None,
        "prediction_type": predict_task.prediction_type,
        "ultrasound_type": predict_task.ultrasound_type,
        "pig_type": predict_task.pig_type,
        "status": predict_task.status,
        "completed_at": predict_task.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if predict_task.completed_at else None,
        "result": predict_task.result,
    } for predict_task in predict_list], total

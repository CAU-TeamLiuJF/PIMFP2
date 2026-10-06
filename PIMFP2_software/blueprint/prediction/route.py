import math
from typing import Union

from flask import g, Response, request

from pimfp import logger
from pimfp.config import config
from pimfp.dto import BackfatReq, LoinEyeReq, DoubleViewReq, PREDICTION000Rsp, PREDICTION001Req, PREDICTION002Req, \
    PREDICTION003Rsp, PREDICTION002Rsp, PREDICTION004Rsp, PREDICTION005Req, PREDICTION005Rsp, PredictTaskResultDTO
from pimfp.entity import BackfatTask, LoinEyeTask, DoubleViewTask, BackfatSummary, LoinEyeSummary, DoubleViewSummary, PigType, \
    PredictionType
from pimfp.error import BizI18nError, PredictionErrCode
from pimfp.helper import jsonapi, bizrspify, safetool, jsonrsp, formreq
from pimfp.helper.ratelimiter import DistributedFixedWindowRateLimiter
from pimfp.middleware.redis import redis, Region
from . import prediction_bp
from .service import prediction_service

_LOGGER = logger.get_logger(__name__)

_PREDICT_TASK_RL = DistributedFixedWindowRateLimiter(
    redis_client=redis,
    window=60 * 60 * 1000,  # 1h
    burst=config.app.get("upload_id_burst_per_hour", 128)
)


@prediction_bp.post('/PREDICTION000', endpoint="PREDICTION000")
@jsonapi(type=Union[BackfatReq, LoinEyeReq, DoubleViewReq])
@bizrspify
def apply_predict(req_data: Union[BackfatReq, LoinEyeReq, DoubleViewReq], _: Response) -> PREDICTION000Rsp:
    allowed, _ = _PREDICT_TASK_RL.try_acquire(identifier=f"{Region.UPLOAD.region}::{g.user.email}")
    if not allowed:
        _LOGGER.warning(f"apply predict task too frequently")
        raise BizI18nError(PredictionErrCode.TOO_MANY_UPLOAD_TASK)

    if isinstance(req_data, BackfatReq):
        predict_task = BackfatTask(
            prediction_type=PredictionType.BACKFAT,
            ultrasound_type=req_data.ultrasound_type,
            pig_type=req_data.pig_type,
            summary_list=[BackfatSummary(
                row_idx=summary.row_idx,
                name=summary.name,
                image=summary.image,
                feature1=summary.feature1,
                feature2=summary.feature2,
            ) for summary in req_data.summary_list],
        )
    elif isinstance(req_data, LoinEyeReq):
        if req_data.pig_type is PigType.LEAN:
            raise BizI18nError(PredictionErrCode.UNSUPPORTED_LOIN_LEAN)

        predict_task = LoinEyeTask(
            prediction_type=PredictionType.LOIN_EYE,
            ultrasound_type=req_data.ultrasound_type,
            pig_type=req_data.pig_type,
            summary_list=[LoinEyeSummary(
                row_idx=summary.row_idx,
                name=summary.name,
                image=summary.image,
                feature=summary.feature,
            ) for summary in req_data.summary_list],
        )
    else:  # DoubleViewReq
        if req_data.pig_type is PigType.LEAN:
            raise BizI18nError(PredictionErrCode.UNSUPPORTED_LOIN_LEAN)

        predict_task = DoubleViewTask(
            prediction_type=PredictionType.BACKFAT_LOIN_EYE,
            ultrasound_type=req_data.ultrasound_type,
            pig_type=req_data.pig_type,
            summary_list=[DoubleViewSummary(
                row_idx=summary.row_idx,
                name=summary.name,
                backfat=summary.backfat,
                loin_eye=summary.loin_eye,
                feature1=summary.feature1,
                feature2=summary.feature2,
                feature3=summary.feature3,
            ) for summary in req_data.summary_list],
        )

    flow_no = prediction_service.apply_predict(predict_task)
    signed_flow_no = safetool.sign_token(config.app.secret_key, flow_no)
    return PREDICTION000Rsp(flow_no=signed_flow_no)


@prediction_bp.post('/PREDICTION001', endpoint="PREDICTION001")
@jsonrsp
@formreq(type=PREDICTION001Req)
@bizrspify
def upload_images(req_data: PREDICTION001Req, _: Response) -> None:
    flow_no = req_data.flow_no
    _LOGGER.info(f"upload chunk with signed flow no:{flow_no}")
    valid, unsigned_flow_no = safetool.verify_token(config.app.secret_key, flow_no)
    if not valid:
        _LOGGER.error(f"invalid signed flow no: {flow_no}")
        raise BizI18nError(PredictionErrCode.BAD_FLOW_NO)

    images = request.files.getlist('images')
    if len(images) <= 0:
        _LOGGER.error(f"no images in request")
        raise BizI18nError(PredictionErrCode.UPLOAD_NO_IMAGES)

    prediction_service.upload_images(unsigned_flow_no, images)


@prediction_bp.post('/PREDICTION002', endpoint="PREDICTION002")
@jsonapi(type=PREDICTION002Req)
@bizrspify
def predict(req_data: PREDICTION002Req, _: Response) -> PREDICTION002Rsp:
    flow_no = req_data.flow_no
    _LOGGER.info(f"predict with signed flow no:{flow_no}")
    valid, unsigned_flow_no = safetool.verify_token(config.app.secret_key, flow_no)
    if not valid:
        _LOGGER.error(f"invalid signed flow no: {flow_no}")
        raise BizI18nError(PredictionErrCode.BAD_FLOW_NO)

    prediction_service.predict(unsigned_flow_no)
    return PREDICTION002Rsp(flow_no=unsigned_flow_no)


@prediction_bp.post('/PREDICTION003', endpoint="PREDICTION003")
@jsonrsp
@bizrspify
def latest_avail_quota(_: Response) -> PREDICTION003Rsp:
    avail_quota = prediction_service.get_latest_avail_quota()
    return PREDICTION003Rsp(avail_quota=avail_quota)


@prediction_bp.post('/PREDICTION004', endpoint="PREDICTION004")
@jsonrsp
@bizrspify
def total_predicted_images(_: Response) -> PREDICTION004Rsp:
    total = prediction_service.get_total_predicted_images()
    return PREDICTION004Rsp(total=total)


@prediction_bp.post('/PREDICTION005', endpoint="PREDICTION005")
@jsonapi(type=PREDICTION005Req)
@bizrspify
def predict_task_list(req_data: PREDICTION005Req, _: Response) -> PREDICTION005Rsp:
    page_no = req_data.page_no
    page_size = req_data.page_size
    status = req_data.status
    predict_list, total = prediction_service.predict_task_list(page_no, page_size, status)

    num = len(predict_list)
    pages = math.ceil(total / page_size)
    tasks = [
        PredictTaskResultDTO(
            flow_no=task["flow_no"],
            submit_at=task["submit_at"],
            prediction_type=task["prediction_type"],
            ultrasound_type=task["ultrasound_type"],
            pig_type=task["pig_type"],
            status=task["status"],
            completed_at=task["completed_at"],
            result=task["result"]
        ) for task in predict_list
    ]
    return PREDICTION005Rsp(num=num, total_num=total, total_pages=pages, tasks=tasks)

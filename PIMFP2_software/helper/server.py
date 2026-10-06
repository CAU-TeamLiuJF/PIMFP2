from datetime import datetime
from zoneinfo import ZoneInfo


def get_server_date() -> datetime:
    return datetime.now(tz=ZoneInfo("Asia/Shanghai"))

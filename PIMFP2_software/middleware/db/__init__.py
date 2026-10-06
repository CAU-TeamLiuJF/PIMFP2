import pymysql
from pymysql.constants import CLIENT

pymysql.install_as_MySQLdb()

from typing import Optional
from pimfp import logger

from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin

class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass

LOGGER = logger.get_logger(__name__)

db: Optional[ReconnectPooledMySQLDatabase] = None


def init_db(config: dict):
    """
    Initialize the db.
    """
    global db

    LOGGER.info(f"initializing db pimfp with config:{config}")
    db = ReconnectPooledMySQLDatabase(**config, client_flag=CLIENT.FOUND_ROWS)

    with db:
        cursor = db.execute_sql("SELECT @@GLOBAL.time_zone, @@SESSION.time_zone")
        result = cursor.fetchall()
        LOGGER.info(f"db pimfp timezone: {result}")
    db.close_all()

    return db


__all__ = [
    "init_db",
    "db",
]

from typing import Optional

from pimfp import logger
from .address import EmailAddress
from .smtp_sender import SMTPSender

LOGGER = logger.get_logger(__name__)

smtp: Optional[SMTPSender] = None


def init_smtp(config) -> SMTPSender:
    """
    Initialize the smtp.
    """
    global smtp

    LOGGER.info(f"initializing smtp with config:{config}")
    smtp = SMTPSender(**config)
    return smtp


__all__ = [
    "init_smtp",
    "smtp",
    "SMTPSender",
    "EmailAddress"
]

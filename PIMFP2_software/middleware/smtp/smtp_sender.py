from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from smtplib import SMTP_SSL
from typing import Optional

from pimfp import logger
from .address import EmailAddress

LOGGER = logger.get_logger(__name__)


class SMTPSender:
    def __init__(self, host: str, port: int, user: str, password: str,
                 from_addr: Optional[str], realname: Optional[str] = None):
        self.host = host
        self.port = port
        self.password = password
        self.user = user
        self.from_addr = from_addr or user
        self.realname = realname

    def send_email(self,
                   to_addrs: list[EmailAddress],
                   cc_addrs: list[EmailAddress] = None,
                   bcc_addrs: list[EmailAddress] = None,
                   subject: Optional[str] = None,
                   content: Optional[MIMEBase] = None,
                   attachments: list[MIMEBase] = None):

        server = SMTP_SSL(self.host, self.port)
        try:
            server.login(self.user, self.password)

            msg_root = MIMEMultipart("mixed")
            msg_root["from"] = formataddr((self.realname, self.from_addr), "utf-8")
            msg_root["to"] = ",".join([formataddr((to.realname, to.email), "utf-8") for to in to_addrs])

            if cc_addrs:
                cc_addrs = ",".join([formataddr((cc.realname, cc.email), "utf-8") for cc in cc_addrs])
                msg_root["cc"] = cc_addrs

            if bcc_addrs:
                bcc_addrs = ",".join([formataddr((bcc.realname, bcc.email), "utf-8") for bcc in bcc_addrs])
                msg_root["bcc"] = bcc_addrs

            if subject:
                msg_root["subject"] = Header(subject, "utf-8")

            if content:
                msg_root.attach(content)

            if attachments:
                for attachment in attachments:
                    msg_root.attach(attachment)

            server.send_message(msg_root)
        finally:
            try:
                server.close()
            except Exception as e:
                LOGGER.warning(f"close smtp server failed", exc_info=e)

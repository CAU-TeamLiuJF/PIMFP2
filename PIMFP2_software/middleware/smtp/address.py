from dataclasses import dataclass

from typing import Optional


@dataclass
class EmailAddress:
    email: str
    realname: Optional[str] = None

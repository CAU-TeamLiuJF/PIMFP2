import base64
import hashlib
import secrets
from typing import Optional

import bcrypt
from itsdangerous import URLSafeSerializer, BadSignature


def bcrypt_hash(plain: str) -> bytes:
    """
    Sign plain text using bcrypt.

    Passing hashpw a string longer than 72 bytes will raise a ValueError instead of silently truncating the string
    following the behavior of the original OpenBSD bcrypt implementation.
    To work around this, a common approach is to hash a string with a cryptographic hash (such as sha256)
    and then base64 encode it to prevent NULL byte problems before hashing the result with bcrypt.
    """
    p = base64.b64encode(hashlib.sha256(plain.encode("UTF-8")).digest())
    return bcrypt.hashpw(p, bcrypt.gensalt(prefix=b"2b"))


def bcrypt_validate(plain: str, hashed: bytes) -> bool:
    """
    Check plain text against hashed result.
    """
    p = base64.b64encode(hashlib.sha256(plain.encode("UTF-8")).digest())
    return bcrypt.checkpw(p, hashed)


def urlsafe_token(nbytes: int) -> str:
    return secrets.token_urlsafe(nbytes)


def sign_token(secret: str, token: str) -> str:
    serializer = URLSafeSerializer(secret)
    return serializer.dumps(token)


def verify_token(secret: str, token: str) -> tuple[bool, Optional[str]]:
    try:
        serializer = URLSafeSerializer(secret)
        return True, serializer.loads(token)
    except BadSignature:
        return False, None

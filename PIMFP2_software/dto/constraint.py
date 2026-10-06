from typing import Annotated

from msgspec import Meta

Email = Annotated[
    str, Meta(
        max_length=254,
        pattern=r"^[a-zA-Z0-9._%+-]{1,64}@(?:[a-zA-Z0-9-]{1,63}\.){1,125}[a-zA-Z0-9]{1,63}$"
    )
]

Password = Annotated[
    str, Meta(
        pattern=r"^(?=.*[a-zA-Z])(?=.*\d)\S{8,255}$"
    )
]

Organization = Annotated[
    str, Meta(
        min_length=1,
        max_length=255,
        pattern=r"^(?=.*\S).{1,255}"
    )
]

RegisterVerifyCode = Annotated[
    str, Meta(
        pattern=r"^.{6}$",
    )
]

LoginVerifyCode = Annotated[
    str, Meta(
        pattern=r"^[A-Z0-9]{6}$"
    )
]

ResetVerifyCode = Annotated[
    str, Meta(
        pattern=r"^[A-Z0-9]{6}$"
    )
]

PredictionType = Annotated[
    int, Meta(
        ge=0,
        le=2
    )
]

UltrasoundType = Annotated[
    int, Meta(
        ge=0,
        le=1
    )
]

PigType = Annotated[
    int, Meta(
        ge=0,
        le=1
    )
]

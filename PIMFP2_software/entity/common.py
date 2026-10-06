from enum import Enum


class SupportedLocaleEnum(Enum):
    ZH_CN = "zh_CN"
    EN_US = "en_US"


SupportedLocaleMap = {locale.value: locale for locale in SupportedLocaleEnum}

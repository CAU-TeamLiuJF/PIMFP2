from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Template

from pimfp.entity import SupportedLocaleEnum
from pimfp.resources import ResourcesReader
from pimfp.helper import captcha

_register_en_US_html = ResourcesReader.resource_text("email/register/index_en_US.html", encoding="utf-8")
_register_en_US_txt = ResourcesReader.resource_text("email/register/index_en_US.txt", encoding="utf-8")
_register_zh_CN_html = ResourcesReader.resource_text("email/register/index_zh_CN.html", encoding="utf-8")
_register_zh_CN_txt = ResourcesReader.resource_text("email/register/index_zh_CN.txt", encoding="utf-8")
_register_en_US_html_template = Template(_register_en_US_html)
_register_en_US_txt_template = Template(_register_en_US_txt)
_register_zh_CN_html_template = Template(_register_zh_CN_html)
_register_zh_CN_txt_template = Template(_register_zh_CN_txt)


def render_register_email(verify_code: str, expire: int, rights_year: str, locale: SupportedLocaleEnum) -> MIMEMultipart:
    kwargs = {
        "verify_code": verify_code,
        "expire": expire,
        "rights_year": rights_year
    }

    if locale is SupportedLocaleEnum.ZH_CN:
        rendered_txt = _register_zh_CN_txt_template.render(**kwargs)
        rendered_html = _register_zh_CN_html_template.render(**kwargs)
    elif locale is SupportedLocaleEnum.EN_US:
        rendered_txt = _register_en_US_txt_template.render(**kwargs)
        rendered_html = _register_en_US_html_template.render(**kwargs)
    else:  # unreachable
        raise ValueError(f"unsupported locale: {locale}")

    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(rendered_txt, "plain", "utf-8"))
    msg.attach(MIMEText(rendered_html, "html", "utf-8"))
    return msg


_register_code_generator = captcha.TextCaptchaGeneratorBuilder() \
    .length(6) \
    .add_digit() \
    .add_uppercase() \
    .build()


def generate_register_code() -> str:
    return _register_code_generator.generate()


_login_en_US_html = ResourcesReader.resource_text("email/login/index_en_US.html", encoding="utf-8")
_login_en_US_txt = ResourcesReader.resource_text("email/login/index_en_US.txt", encoding="utf-8")
_login_zh_CN_html = ResourcesReader.resource_text("email/login/index_zh_CN.html", encoding="utf-8")
_login_zh_CN_txt = ResourcesReader.resource_text("email/login/index_zh_CN.txt", encoding="utf-8")
_login_en_US_html_template = Template(_login_en_US_html)
_login_en_US_txt_template = Template(_login_en_US_txt)
_login_zh_CN_html_template = Template(_login_zh_CN_html)
_login_zh_CN_txt_template = Template(_login_zh_CN_txt)


def render_login_email(verify_code: str, expire: int, rights_year: str, locale: SupportedLocaleEnum) -> MIMEMultipart:
    kwargs = {
        "verify_code": verify_code,
        "expire": expire,
        "rights_year": rights_year
    }

    if locale is SupportedLocaleEnum.ZH_CN:
        rendered_txt = _login_zh_CN_txt_template.render(**kwargs)
        rendered_html = _login_zh_CN_html_template.render(**kwargs)
    elif locale is SupportedLocaleEnum.EN_US:
        rendered_txt = _login_en_US_txt_template.render(**kwargs)
        rendered_html = _login_en_US_html_template.render(**kwargs)
    else:  # unreachable
        raise ValueError(f"unsupported locale: {locale}")

    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(rendered_txt, "plain", "utf-8"))
    msg.attach(MIMEText(rendered_html, "html", "utf-8"))
    return msg


_login_code_generator = captcha.TextCaptchaGeneratorBuilder() \
    .length(6) \
    .add_digit() \
    .add_uppercase() \
    .build()


def generate_login_code() -> str:
    return _login_code_generator.generate()


_reset_en_US_html = ResourcesReader.resource_text("email/reset/index_en_US.html", encoding="utf-8")
_reset_en_US_txt = ResourcesReader.resource_text("email/reset/index_en_US.txt", encoding="utf-8")
_reset_zh_CN_html = ResourcesReader.resource_text("email/reset/index_zh_CN.html", encoding="utf-8")
_reset_zh_CN_txt = ResourcesReader.resource_text("email/reset/index_zh_CN.txt", encoding="utf-8")
_reset_en_US_html_template = Template(_reset_en_US_html)
_reset_en_US_txt_template = Template(_reset_en_US_txt)
_reset_zh_CN_html_template = Template(_reset_zh_CN_html)
_reset_zh_CN_txt_template = Template(_reset_zh_CN_txt)


def render_reset_email(verify_code: str, expire: int, rights_year: str, locale: SupportedLocaleEnum) -> MIMEMultipart:
    kwargs = {
        "verify_code": verify_code,
        "expire": expire,
        "rights_year": rights_year
    }

    if locale is SupportedLocaleEnum.ZH_CN:
        rendered_txt = _reset_zh_CN_txt_template.render(**kwargs)
        rendered_html = _reset_zh_CN_html_template.render(**kwargs)
    elif locale is SupportedLocaleEnum.EN_US:
        rendered_txt = _reset_en_US_txt_template.render(**kwargs)
        rendered_html = _reset_en_US_html_template.render(**kwargs)
    else:  # unreachable
        raise ValueError(f"unsupported locale: {locale}")

    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(rendered_txt, "plain", "utf-8"))
    msg.attach(MIMEText(rendered_html, "html", "utf-8"))
    return msg


_reset_code_generator = captcha.TextCaptchaGeneratorBuilder() \
    .length(6) \
    .add_digit() \
    .add_uppercase() \
    .build()


def generate_reset_code() -> str:
    return _reset_code_generator.generate()

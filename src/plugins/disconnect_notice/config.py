from pydantic import BaseModel, field_validator
from nonebot import get_plugin_config

class Config(BaseModel):
    notice_mail_host: str = "smtp.qq.com"
    notice_mail_user: str = ""
    notice_mail_pass: str = ""

    @field_validator("notice_mail_user", "notice_mail_pass")
    @classmethod
    def check_config(cls, s: str) -> str:
        if s:
            return s
        raise ValueError("user and pass must be configured")

config = get_plugin_config(Config)
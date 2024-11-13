from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    glm_cookie: str = ""
    qwen_cookie: str = ""
    chat_default_identity: str = ""

config = get_plugin_config(Config)
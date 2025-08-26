from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    qqmusic_api_key: str = ""

config = get_plugin_config(Config)

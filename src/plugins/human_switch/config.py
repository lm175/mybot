from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    admin_id: int = 0

config = get_plugin_config(Config)

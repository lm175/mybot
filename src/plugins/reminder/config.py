from pydantic import BaseModel
from nonebot import get_plugin_config

class Config(BaseModel):
    glm_api_key: str = ""
    glm_default_setting: str = ""

config = get_plugin_config(Config)
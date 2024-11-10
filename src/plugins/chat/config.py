from pydantic import BaseModel
from pathlib import Path
from nonebot import get_plugin_config

DATA_PATH = Path(__file__).parent / "data"

class Config(BaseModel):
    glm_cookie: str = ""
    qwen_cookie: str = ""
    chat_default_identity: str = ""

config = get_plugin_config(Config)
from pydantic import BaseModel, validator
from pathlib import Path
from nonebot import get_plugin_config
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

class Config(BaseModel):
    reminder_plugin_enabled: bool = True
    tasks_path: Path = store.get_plugin_data_file("tasks.json")

    """最大时间限制(秒)"""
    limit: int = 2592000


plugin_config = get_plugin_config(Config)
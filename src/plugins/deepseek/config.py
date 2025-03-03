from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    deepseek_api_url: str = 'https://api.deepseek.com'
    deepseek_api_key: str = ''
    deepseek_llm: str = 'deepseek-chat'
    deepseek_vlm: str = 'Qwen/QVQ-72B-Preview'
    deepseek_max_len: int = 20

    kimi_access_token: str = ''
    kimi_refresh_token: str = ''
    

config = get_plugin_config(Config)

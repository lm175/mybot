from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    siliconflow_api_url: str = 'https://api.siliconflow.cn/v1'
    siliconflow_api_key: str = ''
    siliconflow_chat_model: str = 'deepseek-ai/DeepSeek-V3'
    siliconflow_summary_model: str = 'deepseek-ai/DeepSeek-R1'

    deepseek_api_url: str = 'https://api.deepseek.com'
    deepseek_api_key: str = ''
    deepseek_chat_model: str = 'deepseek-chat'
    deepseek_summary_model: str = 'deepseek-reasoner'

    deepseek_max_len: int = 30
    deepseek_max_token: int = 256


config = get_plugin_config(Config)

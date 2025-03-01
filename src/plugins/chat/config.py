from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):
    deepseekapi_api_url: str = 'https://api.siliconflow.cn/v1'
    deepseekapi_api_key: str = ''
    deepseekapi_llm: str = 'deepseek-ai/DeepSeek-V3'
    deepseekapi_vlm: str = 'Qwen/QVQ-72B-Preview'
    deepseekapi_max_len: int = 20
    

config = get_plugin_config(Config)
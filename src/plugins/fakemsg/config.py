from pydantic import BaseModel
from nonebot import get_plugin_config


class Config(BaseModel):

    fakemsg_user_split: str = "+"
    """分隔不同用户的符号"""

    fakemsg_message_split: str = " "
    """分隔同一用户的几条消息"""

    fakemsg_nick_start: str = "【"
    """获取昵称位置的起始符号"""
    
    fakemsg_nick_end:   str = "】"
    """获取昵称位置的终止符号"""


config = get_plugin_config(Config)
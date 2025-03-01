from nonebot import require
require('nonebot_plugin_orm')
from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Text, BigInteger, func

from datetime import datetime


class UserMessage(Model):
    record_id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(BigInteger)
    nickname: Mapped[str] = mapped_column(String(255))
    group_id: Mapped[int] = mapped_column(BigInteger, default=0)
    content: Mapped[str] = mapped_column(Text)
    is_bot_reply: Mapped[bool] = mapped_column(default=False)    # 是否为bot发送的消息
    target_user_id: Mapped[int] = mapped_column(BigInteger, default=0)      # bot发送的目标用户
    is_mentioned: Mapped[bool] = mapped_column(default=False)   # 是否与bot有关
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
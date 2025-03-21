from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Text, DateTime, func

from datetime import datetime


class PrivateMessage(Model):
    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    user_id: Mapped[int] = mapped_column(BigInteger)
    nickname: Mapped[str] = mapped_column(String(255))
    is_bot_msg: Mapped[bool] = mapped_column(default=False)
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class GroupMessage(Model):
    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    group_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    nickname: Mapped[str] = mapped_column(String(255))
    is_bot_msg: Mapped[bool] = mapped_column(default=False)
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# class ChatMessage(Model):
#     message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
#     session_id: Mapped[str] = mapped_column(String(255))
#     user_id: Mapped[int] = mapped_column(BigInteger)
#     group_id: Mapped[int] = mapped_column(BigInteger)
#     nickname: Mapped[str] = mapped_column(String(255))
#     is_bot_msg: Mapped[bool] = mapped_column(default=False)
#     content: Mapped[str] = mapped_column(Text)
#     timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# class UserSession(Model):
#     user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
#     session_id: Mapped[str] = mapped_column(String(255))

# class GroupSession(Model):
#     group_id: Mapped[int] = mapped_column(BigInteger)
#     session_id: Mapped[str] = mapped_column(String(255))

# class UserInfo(Model):
#     user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
#     warning_times: Mapped[int]
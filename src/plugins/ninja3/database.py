from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger
from .requires import Model

from datetime import date


class GameIDs(Model):
    game_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger)


class Users(Model):
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False
    )
    uid_nums: Mapped[int]
    need_remind: Mapped[bool]


class GiftCodes(Model):
    code: Mapped[str] = mapped_column(String(255), primary_key=True)
    time: Mapped[date]
    available: Mapped[bool]
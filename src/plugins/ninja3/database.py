from sqlalchemy.orm import Mapped, mapped_column
from .requires import Model

from datetime import date


class GameIDs(Model):
    game_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int]


class Users(Model):
    user_id: Mapped[int] = mapped_column(primary_key=True)
    uid_nums: Mapped[int]
    need_remind: Mapped[bool]


class GiftCodes(Model):
    code: Mapped[str] = mapped_column(primary_key=True)
    time: Mapped[date]
    available: Mapped[bool]
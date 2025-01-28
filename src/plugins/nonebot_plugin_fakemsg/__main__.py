from nonebot import on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    MessageEvent,
)
from nonebot.log import logger
from httpx import AsyncClient

import re

from .config import config

USER_SPLIT = re.escape(config.fakemsg_user_split)
NICK_START = re.escape(config.fakemsg_nick_start)
NICK_END = re.escape(config.fakemsg_nick_end)
MSG_SPLIT = config.fakemsg_message_split



class User:
    def __init__(self, user_id: int, nick_name: str, messages: list[Message]):
        self.user_id = user_id
        self.nick_name = nick_name
        self.messages = messages


async def get_user_name(bot: Bot, user_id: int) -> str:
    try:
        nick = (await bot.get_stranger_info(user_id=user_id))['nickname']
    except Exception as e:
        logger.error(e)
        try:
            async with AsyncClient() as client:
                res = await client.get(f"https://api.leafone.cn/api/qqnick?qq={user_id}")
                data = res.json()
                nick = data.get("data").get("nickname")
        except Exception as e:
            logger.error(e)
            nick = "QQ用户"
    return nick


async def trans_to_list(msg: Message) -> list[User]:
    """
    将输入Message对象拆分成对应的列表
    """
    s = USER_SPLIT + str(msg)
    pattern = rf'{USER_SPLIT}(\d{{5,10}})({NICK_START}.*?{NICK_END})?说'
    matches: list[str] = re.findall(pattern, s)
    parts: list[str] = re.split(pattern, s)
    users: list[User] = []
    for i in range(1, len(parts), 3):
        user_id, nick_name = matches[i // 3]
        user_id = int(user_id)
        messages = [Message(m) for m in parts[i + 2].split(MSG_SPLIT)]
        users.append(User(user_id, nick_name[1:-1], messages))

    return users




matcher = on_regex(rf'^\d{{5,10}}({NICK_START}.*?{NICK_END})?说', priority=10)

@matcher.handle()
async def _(bot: Bot, event: MessageEvent):
    users = await trans_to_list(event.message)
    messages: Message = Message()
    user_name: dict[int, str] = {}
    for user in users:
        user_id = user.user_id
        if user.nick_name:
            nickname = user.nick_name
        else:
            if user_id in user_name:
                nickname = user_name[user_id]
            else:
                nickname = await get_user_name(bot, user_id)
                user_name[user_id] = nickname
        
        for msg in user.messages:
            messages += MessageSegment.node_custom(
                user_id=user_id,
                nickname=nickname,
                content=msg
            )
    await matcher.send(messages)
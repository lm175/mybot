from nonebot import on_command, on_fullmatch
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent
)
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import delete
import httpx

from .models import PrivateMessage, GroupMessage
from .config import config
from .utils import self_name


base_url = config.deepseek_api_url
api_key = config.deepseek_api_key


show_balance = on_command('show balance', priority=10, block=True, permission=SUPERUSER)

@show_balance.handle()
async def _():
    async with httpx.AsyncClient() as cli:
        resp = await cli.get(
            url=f'{base_url}/user/balance',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        await show_balance.send(str(resp.json()))




clear = on_fullmatch(('clear', '/clear'), rule=to_me(), priority=10, block=True)

@clear.handle()
async def _(event: MessageEvent, session: async_scoped_session):
    if isinstance(event, PrivateMessageEvent):
        await session.execute(
            delete(PrivateMessage)
            .where(PrivateMessage.user_id == event.user_id)
        )
    elif isinstance(event, GroupMessageEvent):
        await session.execute(
            delete(GroupMessage)
            .where(GroupMessage.group_id == event.group_id)
        )
    else:
        return
    await session.commit()
    await clear.send(f'唔.. {self_name}好像忘掉了很多事情呢')



clear_all = on_fullmatch(('clear-all', '/clear-all'), rule=to_me(), priority=5, block=True, permission=SUPERUSER)

@clear_all.handle()
async def _(session: async_scoped_session):
    await session.execute(delete(PrivateMessage))
    await session.execute(delete(GroupMessage))
    await session.commit()
    await clear_all.send('已清空所有用户的对话记录')
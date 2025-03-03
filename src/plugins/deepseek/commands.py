from nonebot import on_command, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    PrivateMessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
)
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, delete, asc
import httpx

import asyncio

from .models import PrivateMessage, GroupMessage
from .config import config
from .utils import self_name

from .revKimi import Chatbot as KimiBot


base_url = config.deepseek_api_url
api_key = config.deepseek_api_key


kimi_bot = KimiBot({
    "access_token": config.kimi_access_token,
    "refresh_token": config.kimi_refresh_token
})
kimi_lock = asyncio.Lock()
def send_kimi_request(prompt: str):
    return kimi_bot.ask(
        prompt=prompt,
        conversation_id='',
        use_search=True
    )



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




summarize = on_fullmatch('总结一下', priority=10, block=True)

@summarize.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    await summarize.send(f'{self_name}正在总结，请稍等一下哦~')
    records = (await session.scalars(
        select(GroupMessage)
        .where(GroupMessage.group_id == event.group_id)
        .order_by(asc(GroupMessage.timestamp))
    )).all()
    system_prompt = f'下面是一段群聊中的消息，格式为[time]nickname: message，请你总结聊天记录的内容，使用自然语言，不要重复原始消息格式'
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in records[-500:]:
        role = 'assistant' if msg.is_bot_msg else 'user'
        content = f'[{msg.timestamp}]{msg.content}'
        messages.append({'role': role, 'content': content})
    async with kimi_lock:
        resp = await asyncio.to_thread(send_kimi_request, str(messages))
        reply_content = f"##推理\n{resp['reasoning_content']}\n\n\n##回复\n{resp['text']}" # type: ignore
    try:
        await summarize.send(MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname=self_name,
            content=Message(MessageSegment.node_custom(
                user_id=int(bot.self_id),
                nickname=self_name,
                content=Message(MessageSegment(
                    type="markdown",
                    data={
                        "content": reply_content
                    }
                ))
            ))
        ))
    except:
        await summarize.send(MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname=self_name,
            content=reply_content
        ))



clear = on_fullmatch(('clear', '/clear'), priority=10, block=True)

@clear.handle()
async def _(event: PrivateMessageEvent, session: async_scoped_session):
    await session.execute(
        delete(PrivateMessage)
        .where(PrivateMessage.user_id == event.user_id)
    )
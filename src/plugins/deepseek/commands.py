from nonebot import on_command, on_fullmatch
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    PrivateMessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
)
from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, delete, asc
from openai import OpenAI
import httpx

import asyncio, re

from .models import PrivateMessage, GroupMessage
from .config import config
from .utils import self_name


SILICONFLOW_API_URL = config.siliconflow_api_url
SILICONFLOW_API_KEY = config.siliconflow_api_key
SILICONFLOW_SUMMARY_MODEL = config.siliconflow_summary_model
DEEPSEEK_API_URL = config.deepseek_api_url
DEEPSEEK_API_KEY = config.deepseek_api_key
DEEPSEEK_SUMMARY_MODEL = config.deepseek_summary_model


siliconflow_client = OpenAI(api_key=SILICONFLOW_API_KEY, base_url=SILICONFLOW_API_URL)
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)

def send_request(messages: list):
    try:
        result = siliconflow_client.chat.completions.create(
            model=SILICONFLOW_SUMMARY_MODEL,
            messages=messages,
            stream=False,
        )
    except:
        result = deepseek_client.chat.completions.create(
            model=DEEPSEEK_SUMMARY_MODEL,
            messages=messages,
            stream=False,
        )
    finally:
        return result



show_balance = on_command('showbalance', priority=10, block=True, permission=SUPERUSER)

@show_balance.handle()
async def _():
    async with httpx.AsyncClient() as cli:
        sf_resp = await cli.get(
            url=f'{SILICONFLOW_API_URL}/user/info',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
            }
        )
        ds_resp = await cli.get(
            url=f'{DEEPSEEK_API_URL}/user/balance',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
            }
        )
        await show_balance.send(f'siliconflow\n{sf_resp.json()}\n\ndeepseek\n{ds_resp.json()}')




summarize = on_fullmatch('总结一下', priority=10, block=True)

@summarize.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    await summarize.send(f'{self_name}正在总结聊天记录，请稍等一下哦~')
    records = (await session.scalars(
        select(GroupMessage)
        .where(GroupMessage.group_id == event.group_id)
        .order_by(asc(GroupMessage.timestamp))
    )).all()
    system_prompt = f'下面是一段群聊中的消息，格式为[time]nickname: message，请你详细总结聊天记录的内容。使用自然语言，回复用中文，可以用markdown，不要重复原始消息格式'
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in records[-200:]:
        role = 'assistant' if msg.is_bot_msg else 'user'
        content = f'[{msg.timestamp}]{msg.content}'
        messages.append({'role': role, 'content': content})
    resp = await asyncio.to_thread(send_request, messages)
    resp_content = str(resp.choices[0].message.content)
    resp_thinking = getattr(resp.choices[0].message, 'reasoning_content', '')
    cleaned_thinking = re.sub(r'\n{2,}', '\n', resp_thinking)
    reply_content = f"#深度思考\n>{cleaned_thinking}\n\n\n#回复\n{resp_content}"
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
    try:
        await session.execute(
            delete(PrivateMessage)
            .where(PrivateMessage.user_id == event.user_id)
        )
        await session.commit()
        await clear.send(f'唔... {self_name}好像忘记了很多事情呢')
    except Exception as e:
        logger.error(e)
        await session.rollback()
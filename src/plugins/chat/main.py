from nonebot import on_message, on_command
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters import Bot
from nonebot.message import event_preprocessor
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    PokeNotifyEvent
)
from nonebot.adapters.onebot.v11 import Bot as obv11Bot
from nonebot import require
require('nonebot_plugin_orm')
from nonebot_plugin_orm import async_scoped_session, get_session
from sqlalchemy import select, delete, or_, asc
from openai import OpenAI

from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio, re

from .models import UserMessage
from .utils import get_str_message, get_random_picture, self_name
from .config import config

API_URL = config.deepseekapi_api_url
API_KEY = config.deepseekapi_api_key

LLM = config.deepseekapi_llm
MAX_LEN = config.deepseekapi_max_len

client = OpenAI(api_key=API_KEY, base_url=API_URL)


dir_path = Path("data/chat/")
if not dir_path.exists():
    dir_path.mkdir(parents=True, exist_ok=True)
character_path = dir_path / 'default_character.txt'
if not character_path.exists():
    character_path.touch()
with open(dir_path / 'default_character.txt', 'r', encoding='utf-8') as f:
    character = f.read()


morning_path = dir_path / 'morning'
if not morning_path.exists():
    morning_path.mkdir(parents=True, exist_ok=True)
night_path = dir_path / 'night'
if not night_path.exists():
    night_path.mkdir(parents=True, exist_ok=True)



def send_request(model: str, messages: list):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
    )



chat = on_message(priority=99, block=False)


@chat.handle()
async def _(session: async_scoped_session, event: MessageEvent):
    # at消息，需回复
    if event.is_tome():
        if isinstance(event, GroupMessageEvent):
            # 获取历史记录
            records = (await session.scalars(
                select(UserMessage)
                .where(UserMessage.group_id == event.group_id)
                .order_by(asc(UserMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是一段群聊中的消息，格式为[time]nickname: message，请你根据自己的设定和聊天记录进行回复，回复时使用自然语言，不要重复原始消息格式'
            messages = [{'role': 'system', 'content': system_prompt}]
            for msg in records[-MAX_LEN:]:
                role = 'assistant' if msg.is_bot_reply else 'user'
                content = f'[{msg.timestamp}]{msg.nickname}: {msg.content}' if msg.message_id else f'[{msg.timestamp}]{msg.content}'
                messages.append({'role': role, 'content': content})

            # 添加本次对话
            current_content = await get_str_message(event, True)
            formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{event.sender.nickname}: {current_content}'})
            session.add(UserMessage(
                user_id=event.user_id,
                nickname=str(event.sender.nickname),
                group_id=event.group_id,
                content=current_content,
                is_mentioned=True
            ))
            await session.commit()

        elif isinstance(event, PrivateMessageEvent):
            # 获取历史记录
            records = (await session.scalars(
                select(UserMessage)
                .where(or_(
                    UserMessage.user_id == event.user_id and UserMessage.is_mentioned,
                    UserMessage.is_bot_reply and UserMessage.target_user_id == event.user_id
                ))
                .order_by(asc(UserMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是你和用户{event.sender.nickname}的对话，格式为[time]message，回复时使用自然语言，不要重复原始消息格式'
            messages = [{'role': 'system', 'content': system_prompt}]
            for msg in records[-MAX_LEN:]:
                role = 'assistant' if msg.is_bot_reply else 'user'
                content = f'[{msg.timestamp}]{msg.content}' if msg.message_id else f'[{msg.timestamp}]{msg.content}'
                messages.append({'role': role, 'content': content})

            # 添加本次对话
            current_content = await get_str_message(event, True)
            formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{current_content}'})
            session.add(UserMessage(
                user_id=event.user_id,
                nickname=str(event.sender.nickname),
                content=current_content,
                is_mentioned=True
            ))
            await session.commit()
        else:
            return

        # 发送api请求并回复
        res = await asyncio.to_thread(send_request, LLM, messages)
        result = res.choices[0].message.content
        if result:
            # 删除开头可能出现的时间和名字冒号
            result = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*', '', result)
            if result.startswith(f'{self_name}:') or result.startswith(f'{self_name}：'):
                result = result[len(self_name)+1:]
            await chat.send(result)
        
        # 简单配图
        msgstr = event.message.extract_plain_text()
        if '早上好' in msgstr or '早安' in msgstr or msgstr == '早':
            pictures = dir_path / "morning"
        elif '晚安' in msgstr:
            pictures = dir_path / "night"
        else:
            await chat.finish()
        pic = await get_random_picture(dir_path / pictures)
        if pic:
            await chat.send(MessageSegment.image(pic))

    # 不回复
    else:
        current_content = await get_str_message(event)
        session.add(UserMessage(
            user_id=event.user_id,
            nickname=str(event.sender.nickname),
            group_id=event.group_id if isinstance(event, GroupMessageEvent) else 0,
            content=current_content,
        ))
        await session.commit()



clear_all = on_command("clear-all", rule=to_me(), priority=9, block=True, permission=SUPERUSER)

@clear_all.handle()
async def _(session: async_scoped_session):
    await session.execute(delete(UserMessage))
    await session.commit()
    await clear_all.send('已清空所有用户的对话记录')





# hook戳一戳和bot调用api发送的消息储存到数据库

@event_preprocessor
async def _(bot: obv11Bot, event: PokeNotifyEvent, session: async_scoped_session):
    sender_name = (await bot.get_stranger_info(user_id=event.sender_id))['nickname'] # type: ignore
    target_user_name = (await bot.get_stranger_info(user_id=event.target_id))['nickname']
    group_id = event.group_id if event.group_id else 0
    content = f'[{sender_name}戳了戳{target_user_name}]'
    msg = UserMessage(
        user_id=event.sender_id, # type: ignore
        nickname=sender_name,
        group_id=group_id,
        content=content
    )
    session.add(msg)
    await session.commit()



@Bot.on_called_api
async def handle_api_result(
    bot: Bot, exception: Optional[Exception], api: str, data: Dict[str, Any], result: Any
):
    if api == 'send_msg':
        session = get_session()
        async with session.begin():
            message_id: int = result['message_id']
            target_user_id: int = data['user_id']
            group_id: int = data.get('group_id', 0)
            message: Message = data['message']
            msg = UserMessage(
                message_id=message_id,
                user_id=int(bot.self_id),
                nickname=self_name,
                group_id=group_id,
                content=await get_str_message(message),
                is_bot_reply=True,
                target_user_id=target_user_id,
            )
            session.add(msg)
            await session.commit()
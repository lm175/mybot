from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Bot,
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageSegment
)
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, asc
from openai import OpenAI

from datetime import datetime
import asyncio, random


from .models import PrivateMessage, GroupMessage
from .config import config
from .const import character, morning_path, night_path
from .utils import (
    self_name,
    get_str_message,
    get_random_picture,
    clean_format
)

API_URL = config.deepseek_api_url
API_KEY = config.deepseek_api_key
LLM = config.deepseek_llm
MAX_LEN = config.deepseek_max_len


client = OpenAI(api_key=API_KEY, base_url=API_URL)

def send_request(model: str, messages: list):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        stream=False,
    )



chat = on_message(rule=to_me(), priority=98, block=True)


@chat.handle()
async def _(bot: Bot, event: PrivateMessageEvent, session: async_scoped_session):
    # 获取历史记录
    records = (await session.scalars(
        select(PrivateMessage)
        .where(PrivateMessage.user_id == event.user_id)
        .order_by(asc(PrivateMessage.timestamp))
    )).all()
    system_prompt = f'{character}\n下面是你和用户{event.sender.nickname}的聊天，格式为[time]message，回复时使用自然语言，不要重复原始消息格式'
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in records[-MAX_LEN:]:
        role = 'assistant' if msg.is_bot_msg else 'user'
        content = f'[{msg.timestamp}]{msg.content}'
        messages.append({'role': role, 'content': content})
    
    # 添加本次对话
    current_content = await get_str_message(bot, event.message)
    if event.reply:
        reply_content = event.reply.message.extract_plain_text()
        if not reply_content:
            reply_content = ['图片']
        current_content = f'(回复“{event.reply.sender.nickname}: {reply_content}”)' + current_content
    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages.append({'role': 'user', 'content': f'[{formatted_now}]{current_content}'})
    session.add(PrivateMessage(
        message_id=event.message_id,
        user_id=event.user_id,
        nickname=str(event.sender.nickname),
        content=current_content
    ))
    await session.commit()

    # 发送api请求并回复
    print(messages)
    response = await asyncio.to_thread(send_request, LLM, messages)
    text = response.choices[0].message.content
    if text:
        parts = clean_format(text)
        result = '' # 存入数据库的content
        for p in parts:
            result += f'{p}\n'
            res = await chat.send(p)

        # 简单配图
        msgstr = event.message.extract_plain_text()
        if '早上好' in msgstr or '早安' in msgstr or msgstr == '早':
            pictures = morning_path
        elif '晚安' in msgstr:
            pictures = night_path
        else:
            await chat.finish()
        pic = await get_random_picture(pictures)
        if pic:
            await chat.send(MessageSegment.image(pic))

        # 保存bot回复的内容
        session.add(PrivateMessage(
            message_id=res['message_id'],
            user_id=event.user_id,
            nickname=self_name,
            is_bot_msg=True,
            content=result
        ))
        await session.commit()




@chat.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    # 没有内容时给出默认回复并reject等待下一句话
    if not str(event.message):
        session.add(GroupMessage(
            message_id=event.message_id,
            group_id=event.group_id,
            user_id=event.user_id,
            nickname=str(event.sender.nickname),
            content=self_name
        ))
        await session.commit()

        default_reply = random.choice([
            '嗯？在呢~（歪头）',
            f'嗯嗯，{self_name}在这里呢(◍•ᴗ•◍)',
            f'{self_name}在哦'
        ])
        res = await chat.send(default_reply)
        session.add(GroupMessage(
            message_id=res['message_id'],
            user_id=event.user_id,
            group_id=event.group_id,
            nickname=self_name,
            is_bot_msg=True,
            content=default_reply
        ))
        await session.commit()
        await chat.reject()

    # 获取历史记录
    records = (await session.scalars(
        select(GroupMessage)
        .where(GroupMessage.group_id == event.group_id)
        .order_by(asc(GroupMessage.timestamp))
    )).all()
    system_prompt = f'{character}\n下面是一段群聊中的消息，格式为[time]nickname: message，请你以聊天记录作为参考回复最后一位用户的消息。回复时不要重复之前说过的内容，使用自然语言，不要重复原始消息格式'
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in records[-MAX_LEN:]:
        role = 'assistant' if msg.is_bot_msg else 'user'
        content = f'[{msg.timestamp}]{msg.nickname}: {msg.content}'
        messages.append({'role': role, 'content': content})
    
    # 添加本次对话
    current_content = f'{self_name}{await get_str_message(bot, event.message)}'
    if event.reply:
        reply_content = event.reply.message.extract_plain_text()
        if not reply_content:
            reply_content = ['图片']
        current_content = f'(回复“{event.reply.sender.nickname}: {reply_content}”)' + current_content
    formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages.append({'role': 'user', 'content': f'[{formatted_now}]{event.sender.nickname}: {current_content}'})
    session.add(GroupMessage(
        message_id=event.message_id,
        group_id=event.group_id,
        user_id=event.user_id,
        nickname=str(event.sender.nickname),
        content=current_content
    ))
    await session.commit()

    # 发送api请求并回复
    print(messages)
    response = await asyncio.to_thread(send_request, LLM, messages)
    text = response.choices[0].message.content
    if text:
        parts = clean_format(text)
        result = '' # 存入数据库的content
        for p in parts:
            result += f'{p}\n'
            res = await chat.send(p)

        # 简单配图
        msgstr = event.message.extract_plain_text()
        if '早上好' in msgstr or '早安' in msgstr or msgstr == '早':
            pictures = morning_path
        elif '晚安' in msgstr:
            pictures = night_path
        else:
            await chat.finish()
        pic = await get_random_picture(pictures)
        if pic:
            await chat.send(MessageSegment.image(pic))

        # 保存bot回复的内容
        session.add(GroupMessage(
            message_id=res['message_id'],
            user_id=event.user_id,
            group_id=event.group_id,
            nickname=self_name,
            is_bot_msg=True,
            content=result
        ))
        await session.commit()



records = on_message(priority=99, block=False)


@records.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    current_content = await get_str_message(bot, event.message)
    if event.reply:
        reply_content = event.reply.message.extract_plain_text()
        if not reply_content:
            reply_content = ['图片']
        current_content = f'(回复“{event.reply.sender.nickname}: {reply_content}”)' + current_content
    session.add(GroupMessage(
        message_id=event.message_id,
        group_id=event.group_id,
        user_id=event.user_id,
        nickname=str(event.sender.nickname),
        content=current_content
    ))
    await session.commit()

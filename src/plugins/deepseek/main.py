from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    MessageSegment
)
from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, delete, asc
from openai import OpenAI

from datetime import datetime, timedelta
import asyncio, random


from .models import PrivateMessage, GroupMessage
from .config import config
from .const import character, blocklist, morning_path, night_path
from .utils import (
    self_name,
    get_str_message,
    get_random_picture,
    clean_format
)

SILICONFLOW_API_URL = config.siliconflow_api_url
SILICONFLOW_API_KEY = config.siliconflow_api_key
SILICONFLOW_CHAT_MODEL = config.siliconflow_chat_model
DEEPSEEK_API_URL = config.deepseek_api_url
DEEPSEEK_API_KEY = config.deepseek_api_key
DEEPSEEK_CHAT_MODEL = config.deepseek_chat_model

MAX_LEN = config.deepseek_max_len
MAX_TOKEN = config.deepseek_max_token

siliconflow_client = OpenAI(api_key=SILICONFLOW_API_KEY, base_url=SILICONFLOW_API_URL)
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)

def send_request(messages: list):
    try:
        result = siliconflow_client.chat.completions.create(
            model=SILICONFLOW_CHAT_MODEL,
            messages=messages,
            stream=False,
            max_tokens=MAX_TOKEN
        )
    except:
        result = deepseek_client.chat.completions.create(
            model=DEEPSEEK_CHAT_MODEL,
            messages=messages,
            stream=False,
            max_tokens=MAX_TOKEN
        )
    finally:
        return result


user_messages: dict[int, bool] = {}
user_block_times: dict[int, list[datetime]] = {}
blocked_users: dict[int, datetime] = {}


chat = on_message(rule=to_me(), priority=98, block=True)


@chat.handle()
async def _(bot: Bot, event: MessageEvent, session: async_scoped_session):
    user_id = event.user_id
    now = datetime.now()
    # 检查是否在屏蔽名单
    if user_id in blocked_users:
        if now < blocked_users[user_id]:
            await chat.finish()
        else:
            del blocked_users[user_id]
    # 违禁词检测
    text = str(event.message)
    for s in blocklist:
        if s in text:
            await chat.send(random.choice([
                '呜哇~你在说什么奇怪的话啦！（假装没看到）',
                '不可以发这种奇怪的东西啦！（捂住耳朵）',
            ]))
            
            if user_id not in user_block_times:
                user_block_times[user_id] = []
            times = user_block_times[user_id]

            # 检查最近一小时内触发违禁词的次数
            recent_times = [time for time in times if now - time < timedelta(hours=1)]
            if len(recent_times) >= 10:
                if isinstance(event, PrivateMessageEvent):
                    await session.execute(
                        delete(PrivateMessage)
                        .where(PrivateMessage.user_id == user_id)
                    )
                    await session.commit()
                blocked_users[user_id] = now + timedelta(hours=1)
                await chat.send(f'(系统提示：用户{user_id}违规次数过多，已屏蔽一小时)')
            else:
                recent_times.append(now)
                user_block_times[user_id] = recent_times

            return
    
    if event.user_id not in user_messages:
        user_messages[event.user_id] = True
    try:
        # 没有内容时给出默认回复并reject等待下一句话
        if isinstance(event, GroupMessageEvent) and not str(event.message):
            session.add(GroupMessage(
                message_id=event.message_id,
                group_id=event.group_id,
                user_id=event.user_id,
                nickname=str(event.sender.nickname),
                content=self_name
            ))
            await session.flush()

            default_reply = random.choice([
                '嗯？在呢~(๑・ω・๑)',
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
        if isinstance(event, GroupMessageEvent):
            records = (await session.scalars(
                select(GroupMessage)
                .where(GroupMessage.group_id == event.group_id)
                .order_by(asc(GroupMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是一段群聊中的消息，格式为[time]nickname: message，请你以聊天记录作为参考回复最后一位用户的消息。回复时使用自然语言，不要重复之前说过的内容，不要重复原始消息格式。'
            messages = [{'role': 'system', 'content': system_prompt}]
        else:
            records = (await session.scalars(
                select(PrivateMessage)
                .where(PrivateMessage.user_id == event.user_id)
                .order_by(asc(PrivateMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是你和一位用户的聊天，格式为[time]message，回复时使用自然语言，不要重复之前说过的内容，不要重复原始消息格式。'
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': f'我是{event.sender.nickname}'}]
        for msg in records[-MAX_LEN:]:
            role = 'assistant' if msg.is_bot_msg else 'user'
            content = f'[{msg.timestamp}]{msg.nickname}: {msg.content}'
            messages.append({'role': role, 'content': content})

        # 添加本次对话
        current_content = f'{self_name}{await get_str_message(bot, event)}'
        if event.reply:
            reply_content = event.reply.message.extract_plain_text()
            if not reply_content:
                reply_content = ['图片']
            current_content = f'(回复“{event.reply.sender.nickname}: {reply_content}”)' + current_content
        formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(event, GroupMessageEvent):
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{event.sender.nickname}: {current_content}'})
            session.add(GroupMessage(
                message_id=event.message_id,
                group_id=event.group_id,
                user_id=event.user_id,
                nickname=str(event.sender.nickname),
                content=current_content
            ))
        else:
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{current_content}'})
            session.add(PrivateMessage(
                message_id=event.message_id,
                user_id=event.user_id,
                nickname=str(event.sender.nickname),
                content=current_content
            ))
        await session.flush()

        # 检查上次对话是否已经结束
        if not user_messages[event.user_id]:
            await session.commit()
            return await chat.finish(f"{event.sender.nickname}同学问得太快啦，{self_name}还没说完呢！")
        else:
            user_messages[event.user_id] = False

        # 发送api请求并回复
        print(messages)
        response = await asyncio.to_thread(send_request, messages)
        reply_text = response.choices[0].message.content
        if reply_text:
            parts = clean_format(reply_text)
            result = '' # 存入数据库的content
            reply_message_id = 0
            for p in parts:
                result += f'{p}\n'
                res = await chat.send(p)
                reply_message_id = res['message_id']
            user_messages[event.user_id] = True

            # 保存bot回复的内容
            if isinstance(event, GroupMessageEvent):
                session.add(GroupMessage(
                    message_id=reply_message_id,
                    user_id=event.user_id,
                    group_id=event.group_id,
                    nickname=self_name,
                    is_bot_msg=True,
                    content=result
                ))
            else:
                session.add(PrivateMessage(
                    message_id=reply_message_id,
                    user_id=event.user_id,
                    nickname=self_name,
                    is_bot_msg=True,
                    content=result
                ))
            await session.commit()

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

    except Exception as e:
        logger.error(e)
        await session.rollback()




records = on_message(priority=99, block=False)


@records.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    try:
        current_content = await get_str_message(bot, event)
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
    except Exception as e:
        logger.error(e)
        await session.rollback()

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
from nonebot.exception import FinishedException
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, delete, asc
from openai import OpenAI

from datetime import datetime, timedelta
import asyncio, random


from .models import PrivateMessage, GroupMessage
from .config import config
from .const import *
from .utils import (
    self_name,
    get_str_message,
    get_random_picture,
    get_random_reply,
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


class ManageDict:
    lock = asyncio.Lock()
    dict_ = {}

class SessionStatus(ManageDict):
    dict_: dict[str, bool] = {}
class PendingMessages(ManageDict):
    dict_: dict[int, list[dict[str, str]]] = {}
# class BlockTimes(ManageDict):
#     dict_: dict[int, list[datetime]] = {}
# class BlockUsers(ManageDict):
#     dict_: dict[int, datetime] = {}

session_status = SessionStatus()    # 标记上一次对话是否已经结束
pending_messages = PendingMessages()    # 用户待处理消息
# block_times = BlockTimes()  # 记录用户触发违禁词的时间
# blocked_users = BlockUsers()    # 屏蔽名单


chat = on_message(rule=to_me(), priority=98, block=True)


@chat.handle()
async def _(bot: Bot, event: MessageEvent, session: async_scoped_session):
    user_id = event.user_id
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    user_name = str(event.sender.nickname)
    # now = datetime.now()
    # # 检查是否在屏蔽名单
    # async with blocked_users.lock:
    #     if user_id in blocked_users.dict_:
    #         if now < blocked_users.dict_[user_id]:
    #             await chat.finish()
    #         else:
    #             del blocked_users.dict_[user_id]
    # 违禁词检测
    text = str(event.message)
    for s in blocklist:
        if s in text:
            await chat.send(await get_random_reply(blocklist_resplies, user_name))
            
            # async with block_times.lock:
            #     if user_id not in block_times.dict_:
            #         block_times.dict_[user_id] = []
            #     times = block_times.dict_[user_id]

            #     # 检查最近一小时内触发违禁词的次数
            #     recent_times = [time for time in times if now - time < timedelta(hours=1)]
            #     if len(recent_times) >= 5:
            #         async with blocked_users.lock:
            #             blocked_users.dict_[user_id] = now + timedelta(hours=1)
            #         if group_id:
            #             await chat.send(f'(用户{user_id}违规次数过多，已屏蔽一小时)')
            #         else:
            #             await session.execute(
            #                 delete(PrivateMessage)
            #                 .where(PrivateMessage.user_id == user_id)
            #             )
            #             await session.commit()
            #             await chat.send(f'(用户{user_id}违规次数过多，已清空对话记录并屏蔽一小时)')
            #     else:
            #         recent_times.append(now)
            #         block_times.dict_[user_id] = recent_times

            return
    
    session_id = f'{user_id}_{group_id}' if group_id else str(user_id)
    async with session_status.lock:
        if session_id not in session_status.dict_:
            session_status.dict_[session_id] = True

    # 没有内容时给出默认回复并reject等待下一句话
    if group_id and not str(event.message) and not event.reply:
        try:
            session.add(GroupMessage(
                message_id=event.message_id,
                group_id=group_id,
                user_id=user_id,
                nickname=user_name,
                content=self_name
            ))
            await session.flush()

            default_reply = await get_random_reply(default_replies, user_name)
            res = await chat.send(default_reply)
            session.add(GroupMessage(
                message_id=res['message_id'],
                user_id=user_id,
                group_id=group_id,
                nickname=self_name,
                is_bot_msg=True,
                content=default_reply
            ))
            await session.commit()
        except Exception as e:
            logger.error(e)
            await session.rollback()
        finally:
            await chat.reject()

    try:
        # 获取历史记录
        if group_id:
            records = (await session.scalars(
                select(GroupMessage)
                .where(GroupMessage.group_id == group_id)
                .order_by(asc(GroupMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是一段群聊中的消息，格式为[time]nickname: message，请你以聊天记录作为参考回复最后一位用户的消息，可适当模仿用户的消息格式。'
            messages = [{'role': 'system', 'content': system_prompt}]
        else:
            records = (await session.scalars(
                select(PrivateMessage)
                .where(PrivateMessage.user_id == user_id)
                .order_by(asc(PrivateMessage.timestamp))
            )).all()
            system_prompt = f'{character}\n下面是你和一位用户的聊天，格式为[time]message，请你根据自己的设定进行回复，可适当模仿用户的消息格式。'
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': f'我是{event.sender.nickname}'}]
        for msg in records[-MAX_LEN:]:
            role = 'assistant' if msg.is_bot_msg else 'user'
            content = f'[{msg.timestamp}]{msg.nickname}: {msg.content}' if group_id else f'[{msg.timestamp}]{msg.content}'
            messages.append({'role': role, 'content': content})

        # 添加本次对话
        message_str = await get_str_message(bot, event)
        formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if group_id:
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{event.sender.nickname}: {message_str}'})
            session.add(GroupMessage(
                message_id=event.message_id,
                group_id=group_id,
                user_id=user_id,
                nickname=str(event.sender.nickname),
                content=message_str
            ))
        else:
            messages.append({'role': 'user', 'content': f'[{formatted_now}]{message_str}'})
            session.add(PrivateMessage(
                message_id=event.message_id,
                user_id=user_id,
                nickname=str(event.sender.nickname),
                content=message_str
            ))
        await session.flush()

        # 检查上次对话是否已经结束
        if not session_status.dict_[session_id]:
            await session.commit()
            if group_id:
                await chat.send(await get_random_reply(busy_replies, user_name))
            else:
                async with pending_messages.lock:
                    pending_messages.dict_[user_id] = messages
            return
        
        async with session_status.lock:
            session_status.dict_[session_id] = False
        try:
            while messages:
                # 发送api请求
                logger.info(messages)
                try:
                    response = await asyncio.to_thread(send_request, messages)
                    reply_text = response.choices[0].message.content
                    logger.info(reply_text)
                except:
                    reply_text = None

                # 回复
                if reply_text:
                    result_messages, result_str = await clean_format(reply_text)
                    reply_message_id = 0
                    for msg in result_messages:
                        res = await chat.send(msg)
                        reply_message_id = res['message_id']

                    # 保存bot回复的内容
                    if group_id:
                        session.add(GroupMessage(
                            message_id=reply_message_id,
                            user_id=user_id,
                            group_id=group_id,
                            nickname=self_name,
                            is_bot_msg=True,
                            content=result_str
                        ))
                        messages = None
                    else:
                        session.add(PrivateMessage(
                            message_id=reply_message_id,
                            user_id=user_id,
                            nickname=self_name,
                            is_bot_msg=True,
                            content=result_str
                        ))
                        # 获取暂存的消息
                        async with pending_messages.lock:
                            if messages := pending_messages.dict_.get(user_id):
                                del pending_messages.dict_[user_id]
                                formatted_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                messages.insert(-1, {'role': 'assistant', 'content': f'[{formatted_now}]{result_str}'})
                    await session.flush()

                    # 简单配图
                    msgstr = event.message.extract_plain_text()
                    if '早上好' in msgstr or '早安' in msgstr or msgstr == '早':
                        pic = await get_random_picture(morning_path)
                    elif '晚安' in msgstr:
                        pic = await get_random_picture(night_path)
                    else:
                        pic = None
                    if pic:
                        await chat.send(MessageSegment.image(pic))
        except Exception as e:
            logger.error(e)
        finally:
            async with session_status.lock:
                session_status.dict_[session_id] = True
        await session.commit()

    except FinishedException:
        pass
    except Exception as e:
        logger.error(e)
        await session.rollback()
        await chat.send(await get_random_reply(error_replies, user_name))




records = on_message(priority=99, block=False)


@records.handle()
async def _(bot: Bot, event: GroupMessageEvent, session: async_scoped_session):
    try:
        message_str = await get_str_message(bot, event)
        session.add(GroupMessage(
            message_id=event.message_id,
            group_id=event.group_id,
            user_id=event.user_id,
            nickname=str(event.sender.nickname),
            content=message_str
        ))
        await session.commit()
    except Exception as e:
        logger.error(e)
        await session.rollback()

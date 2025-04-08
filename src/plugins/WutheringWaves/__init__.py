import os
import re
import asyncio
from pathlib import Path
from copy import deepcopy
from base64 import b64encode
from collections import OrderedDict
from typing import Any, List, Union, Optional

import aiofiles
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent
)
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.internal.adapter import Event
from websockets.exceptions import ConnectionClosed
from nonebot import on, require, on_notice, on_message, on_fullmatch, on_startswith

require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler  # noqa:E402

from .client import GsClient, driver  # noqa:E402
from .auto_install import start, install  # noqa:E402
from .models import Message, MessageReceive  # noqa:E402


__plugin_meta__ = PluginMetadata(
    name="鸣潮查询",
    description="全功能鸣潮查询插件",
    usage=(
        "发送“ww帮助”查看功能列表"
    ),
)

gsclient: Optional[GsClient] = None
command_start = deepcopy(driver.config.command_start)
command_start.discard('')
msg_id_cache = OrderedDict()


async def connect():
    global gsclient
    try:
        gsclient = await GsClient().async_connect()
        await gsclient.start()
    except ConnectionRefusedError:
        logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')



wwcmd = on_startswith(("ww", "WW", "鸣潮", "库洛"), priority=1, block=True)

@wwcmd.handle()
async def _(bot: Bot, ev: MessageEvent):
    if gsclient is None:
        return await connect()
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()

    # 通用字段获取
    group_id = None
    user_id = ev.get_user_id()
    messages = ev.get_message()
    logger.debug(ev)

    self_id = str(bot.self_id)
    message: List[Message] = []
    sp_bot_id: Optional[str] = None

    pm = 6
    msg_id = ''

    if isinstance(ev, GroupMessageEvent) or isinstance(
        ev, PrivateMessageEvent
    ):
        messages = ev.original_message
        msg_id = str(ev.message_id)
        if ev.sender.role == 'owner':
            pm = 2
        elif ev.sender.role == 'admin':
            pm = 3

        sender = ev.sender.dict(exclude_none=True)
        sender['avatar'] = f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640'

        if isinstance(ev, GroupMessageEvent):
            user_type = 'group'
            group_id = str(ev.group_id)
        else:
            user_type = 'direct'
    else:
        logger.debug('[gsuid] 不支持该 onebotv11 事件...')
        return


    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = messages.__class__.__module__.split('.')[2]

    # 确认超管权限
    if await SUPERUSER(bot, ev):
        pm = 1

    # 如果有at提及，增加AT
    if ev.is_tome():
        message.append(Message('at', self_id))

    # 处理消息
    for index, _msg in enumerate(messages):
        message = await convert_message(_msg, message, index, bot)

    if not message:
        return
    msg = MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender=sender,
        content=message,
        msg_id=msg_id if msg_id else '',
        user_pm=pm,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)



async def file_to_base64(file_path: Path):
    # 读取文件内容
    async with aiofiles.open(str(file_path), 'rb') as file:
        file_content = await file.read()

    # 将文件内容转换为base64编码
    base64_encoded = b64encode(file_content)

    # 将base64编码的字节转换为字符串
    base64_string = base64_encoded.decode('utf-8')

    return base64_string



async def convert_message(
    _msg: Any,
    message: List[Message],
    index: int,
    bot: Bot,
):
    if _msg.type == 'text' or _msg.type == 'kmarkdown':
        data: str = (
            _msg.data['text'] if 'text' in _msg.data else _msg.data['content']
        )

        if index == 0 or index == 1:
            for word in command_start:
                _data = data.strip()
                if _data.startswith(word):
                    data = _data[len(word) :]  # noqa:E203
                    break
        message.append(Message('text', data))
    elif _msg.type == 'file':
        if 'file_id' in _msg.data:
            name = _msg.data.get('file')
            if float(_msg.data['file_size']) <= 1024 * 1024 * 4:
                val_data = await bot.call_api(
                    'get_file',
                    file_id=_msg.data.get('file_id'),
                )
                if 'base64' in val_data and val_data['base64']:
                    val = val_data['base64']
                else:
                    path = Path(val_data['file'])
                    val = await file_to_base64(path)
                message.append(Message('file', f'{name}|{val}'))
    elif _msg.type == 'image':
        file_id = _msg.data.get('file_id')
        if file_id in _msg.data.values():
            message.append(Message('image', _msg.data['file_id']))
            logger.debug('[OB12图片]', _msg.data['file_id'])
        elif 'path' in _msg.data:
            message.append(Message('image', _msg.data['path']))
        elif 'file' in _msg.data and 'url' not in _msg.data:
            message.append(Message('image', _msg.data['file']))
        else:
            message.append(Message('image', _msg.data['url']))
    elif _msg.type == 'at':
        message.append(Message('at', _msg.data['qq']))
    elif _msg.type == 'reply':
        message_id = _msg.data.get('message_id')
        if message_id in _msg.data.values():
            message.append(Message('reply', _msg.data['message_id']))
        else:
            message.append(Message('reply', _msg.data['id']))
    elif _msg.type == 'mention':
        if 'user_id' in _msg.data:
            message.append(Message('at', _msg.data['user_id']))
    elif _msg.type == 'wx.link':
        data: str = f"title: {_msg.data['title']} url: {_msg.data['url']}"
        message.append(Message('text', data))
    return message
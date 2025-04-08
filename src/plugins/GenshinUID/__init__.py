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
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.internal.adapter import Event
from websockets.exceptions import ConnectionClosed
from nonebot import on, require, on_notice, on_message, on_fullmatch

require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler  # noqa:E402

from .client import GsClient, driver  # noqa:E402
from .auto_install import start, install  # noqa:E402
from .models import Message, MessageReceive  # noqa:E402

get_message = on_message(priority=999)
get_notice = on_notice(priority=999)
get_tn = on('inline')
install_core = on_fullmatch(
    'gs一键安装',
    permission=SUPERUSER,
    block=True,
)
start_core = on_fullmatch(
    '启动core',
    permission=SUPERUSER,
    block=True,
)
connect_core = on_fullmatch(
    ('连接core', '链接core'),
    permission=SUPERUSER,
    block=True,
)

__plugin_meta__ = PluginMetadata(
    name="GenshinUID",
    description="SayuCore连接器, 支持大部分适配器的全功能插件",
    usage="支持大部分适配器连接SayuCore",
    type="application",
    homepage="https://docs.sayu-bot.com",
    supported_adapters=None,
)

gsclient: Optional[GsClient] = None
command_start = deepcopy(driver.config.command_start)
command_start.discard('')
msg_id_cache = OrderedDict()

if hasattr(driver.config, 'gsuid_core_repeat'):
    is_repeat = True
else:
    is_repeat = False


async def file_to_base64(file_path: Path):
    # 读取文件内容
    async with aiofiles.open(str(file_path), 'rb') as file:
        file_content = await file.read()

    # 将文件内容转换为base64编码
    base64_encoded = b64encode(file_content)

    # 将base64编码的字节转换为字符串
    base64_string = base64_encoded.decode('utf-8')

    return base64_string


@get_tn.handle()
@get_notice.handle()
async def get_notice_message(bot: Bot, ev: Event):
    if gsclient is None:
        return await connect()
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()
    raw_data = ev.dict()
    logger.debug(raw_data)

    try:
        user_id = str(ev.get_user_id())
    except ValueError:
        user_id = '未知'

    group_id = None
    sp_user_type = None
    sp_bot_id = None
    self_id = str(bot.self_id)
    sender = {}
    msg_id = ''
    pm = 6

    if await SUPERUSER(bot, ev):
        pm = 1

    if 'group_id' in raw_data:
        group_id = str(raw_data['group_id'])

    if 'user_id' in raw_data:
        user_id = str(raw_data['user_id'])

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = ev.__class__.__module__.split('.')[2]

    user_type = 'group' if group_id else 'direct'

    if bot.adapter.get_name() == 'OneBot V11':
        if 'notice_type' in raw_data and raw_data['notice_type'] in [
            'group_upload',
            'offline_file',
        ]:
            if 'url' in raw_data['file']:
                val = raw_data['file']['url']
            elif 'id' in raw_data['file']:
                if raw_data['file']['size'] <= 1024 * 1024 * 4:
                    val_data = await bot.call_api(
                        'get_file',
                        file_id=raw_data['file']['id'],
                    )
                    if 'base64' in val_data and val_data['base64']:
                        val = val_data['base64']
                    else:
                        path = Path(val_data['file'])
                        val = await file_to_base64(path)
            else:
                logger.debug(raw_data)
                logger.warning('[文件上传] 不支持的协议端')
                return

            name = raw_data['file']['name']
            message = [Message('file', f'{name}|{val}')]
            # onebot_v11
        else:
            return
    else:
        return
    msg = MessageReceive(
        bot_id=sp_bot_id if sp_bot_id else bot_id,
        bot_self_id=self_id,
        user_type=sp_user_type if sp_user_type else user_type,
        group_id=group_id,
        user_id=user_id,
        sender=sender,
        content=message,
        msg_id=msg_id,
        user_pm=pm,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)


async def handle_message(bot: Bot, ev: Event):
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


@get_message.handle()
async def get_all_message(bot: Bot, ev: Event):
    await handle_message(bot, ev)


@install_core.handle()
async def send_install_msg(matcher: Matcher):
    await matcher.send('即将开始安装...会持续一段时间, 且期间无法使用Bot!')
    await matcher.send(await install())


@connect_core.handle()
async def send_connect_msg(matcher: Matcher):
    await connect()
    await matcher.send('链接成功！')


@start_core.handle()
async def send_start_msg(matcher: Matcher):
    await matcher.send(await start())


@driver.on_bot_connect
async def start_client():
    if gsclient is None:
        await connect()


async def connect():
    global gsclient
    try:
        gsclient = await GsClient().async_connect()
        await gsclient.start()
    except ConnectionRefusedError:
        logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')


@scheduler.scheduled_job('cron', second='*/10')
async def repeat_connect():
    if is_repeat:
        global gsclient
        if gsclient is None:
            await connect()
        else:
            try:
                await gsclient.ws.ensure_open()
            except ConnectionClosed:
                return await connect()
        return


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


# 读取文件为base64
async def convert_file(
    content: Union[Path, str, bytes], file_name: str
) -> Message:
    if isinstance(content, Path):
        async with aiofiles.open(str(content), 'rb') as fp:
            file = await fp.read()
    elif isinstance(content, bytes):
        file = content
    else:
        async with aiofiles.open(content, 'rb') as fp:
            file = await fp.read()
    return Message(
        type='file',
        data=f'{file_name}|{b64encode(file).decode()}',
    )


# 获取文件
async def get_file(bot: Bot, file_id: str):
    data = await bot.call_api(
        api='get_file',
        file_id=f'{file_id}',
        type='path',
    )
    return data

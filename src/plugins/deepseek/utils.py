from nonebot import get_driver
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment
)
from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session
from sqlalchemy import select, desc

from pathlib import Path
from typing import Union, Optional
import json, random, re

from .models import GroupMessage
from .const import images_path


bot_names = list(get_driver().config.nickname)
self_name = bot_names[0] if bot_names else 'bot'
if self_name.startswith('@'):
    self_name = self_name[1:]
with open(Path(__file__).parent / 'resources' / 'face_id.json', encoding='utf-8') as f:
    face_to_str: dict[str, str] = json.load(f)
    str_to_face = {v: k for k, v in face_to_str.items()}


async def get_user_name(user_id: int) -> Union[str, None]:
    "尝试从数据库中寻找用户昵称记录"
    session = get_session()
    async with session.begin():
        result = await session.scalars(
            select(GroupMessage.nickname)
            .where(GroupMessage.user_id == user_id)
            .order_by(desc(GroupMessage.timestamp))
            .limit(1)
        )
        return result.first()


async def get_str_message(bot: Bot, event: MessageEvent) -> str:
    """将MessageEvent处理成模型可理解的文本格式"""
    async def _get_str(message: Message) -> str:
        message_str = ''
        for seg in message:
            msg_type = seg.type
            if msg_type == 'text':
                message_str += seg.data['text']
            elif msg_type == 'face':
                face_id = str(seg.data['id'])
                if desc := face_to_str.get(face_id, ''):
                    message_str += f'[/{desc}]'
            elif msg_type == 'image':
                if summary := seg.data.get('summary'):
                    message_str += summary
                else:
                    message_str += f'[图片]'
            elif msg_type == 'at':
                target_user = ''
                if seg.data['qq'] == 'all':
                    target_user = '全体成员'
                else:
                    try:
                        user_info = await bot.get_stranger_info(user_id=seg.data['qq'])
                        target_user = user_info['nickname']
                    except:
                        if nickname := await get_user_name(seg.data['qq']):
                            target_user = nickname
                        else:
                            target_user = seg.data['qq']
                message_str += f'@{target_user} '
            else:
                message_str += str(seg)
        
        return message_str
    

    result = await _get_str(event.message)
    if event.is_tome() and isinstance(event, GroupMessageEvent):
        result = self_name + result
    if event.reply:
        reply_content = await _get_str(event.reply.message)
        result = f'[回复“{event.reply.sender.nickname}: {reply_content}”]' + result

    return result



async def clean_format(text: str) -> tuple[list[Message], str]:
    """将模型返回的文本处理成Message列表"""
    # 删除开头可能出现时间戳
    pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
    parts: list[str] = re.split(pattern, text)
    if len(parts) >= 2:
        parts = parts[1:]
    result_msg: list[Message] = []
    result_str: str = ''
    for part in parts:
        # 删除可能出现的名字冒号
        user_name = re.search(r'^(.*?)[：:]', part)
        if user_name:
            if user_name.group(1) == self_name:
                part = part[user_name.end():].lstrip()
            else:
                continue
        result_str += part

        # 消息段拼接
        message = Message()
        segments: list[str] = re.split(r'\[(.*?)\]', part)
        for i in range(len(segments)):
            segment = segments[i]
            if not segment:
                continue
            if i % 2 == 0:  # 文本
                message += segment
            else:
                if segment.startswith('/'): # 表情
                    face_name = segment[1:]
                    if face_name in str_to_face:
                        message += MessageSegment.face(int(str_to_face[face_name]))
                    else:
                        message += f'[{segment}]'
                elif segment == '动画表情':
                    image = await get_random_picture(images_path)
                    if image:
                        message += MessageSegment.image(image)
                    else:
                        message += '[动画表情]'
                elif segment.startswith('回复'):
                    pass
                else:
                    message += f'[{segment}]'
        result_msg.append(Message(message))
    return result_msg, result_str


async def get_random_picture(path: Path) -> Path | None:
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a valid directory.")

    files = [file for file in path.iterdir() if file.is_file()]
    if not files:
        return None
    return random.choice(files)


async def get_random_reply(replies: list[str], user_name: str) -> str:
    result = random.choice(replies)
    result = result.replace('{me}', self_name).replace('{user}', user_name)
    return result
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent
)

from pathlib import Path
from typing import Union
import json, random, re




bot_names = list(get_driver().config.nickname)
self_name = bot_names[0] if bot_names else 'bot'
with open(Path(__file__).parent / 'resources' / 'face_id.json', encoding='utf-8') as f:
    faces: dict[str, str] = json.load(f)



async def get_str_message(bot: Bot, message: Message) -> str:
    message_str = ''

    for seg in message:
        msg_type = seg.type
        if msg_type == 'text':
            message_str += seg.data['text']
        elif msg_type == 'face':
            face_id = str(seg.data['id'])
            if desc := faces.get(face_id, ''):
                message_str += f'[/{desc}]'
        elif msg_type == 'image':
            if summary := seg.data.get('summary'):
                message_str += summary
            else:
                message_str += f'[图片]'
        elif msg_type == 'at':
            user_info = await bot.get_stranger_info(user_id=seg.data['qq'])
            message_str += f"@{user_info['nickname']}"
        else:
            message_str += str(seg)

    return message_str



def clean_format(text: str) -> list[str]:
    # 删除开头可能出现时间戳
    pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
    parts = re.split(pattern, text)
    if len(parts) >= 2:
        parts = parts[1:]
    result = []
    for p in parts:
        # 删除可能出现的名字冒号
        if p.startswith(f'{self_name}:') or p.startswith(f'{self_name}：'):
            p = p[len(self_name)+1:]
        result.append(p.strip())
    return result


async def get_random_picture(path: Path) -> Path | None:
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a valid directory.")

    files = [file for file in path.iterdir() if file.is_file()]
    if not files:
        return None
    return random.choice(files)

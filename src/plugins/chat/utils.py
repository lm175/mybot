from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from openai import OpenAI
import httpx

from pathlib import Path
from typing import Union
import json, random, base64


from .config import config

API_URL = config.deepseekapi_api_url
API_KEY = config.deepseekapi_api_key

VLM = config.deepseekapi_vlm

client = OpenAI(api_key=API_KEY, base_url=API_URL)


bot_names = list(get_driver().config.nickname)
self_name = bot_names[0] if bot_names else 'bot'
with open(Path(__file__).parent / 'resource' / 'face_id.json', encoding='utf-8') as f:
    faces: dict[str, str] = json.load(f)



async def describe_image(img_url: str) -> str:
    print(img_url)
    async with httpx.AsyncClient() as cli:
        response = await cli.get(img_url)
        if response.status_code == 200:
            # 将图片内容转换为Base64编码
            base64_str = base64.b64encode(response.content).decode('utf-8')
        else:
            raise Exception(f"Failed to fetch image: HTTP {response.status_code}")

    res = client.chat.completions.create(
        model=VLM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "描述图片中的内容"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_str}"
                    }
                }
            ]
        }],
        stream=False,
    )
    return str(res.choices[0].message.content)



async def get_str_message(obj: Union[MessageEvent, Message], desc_image: bool = False) -> str:
    message_str = ''

    if isinstance(obj, MessageEvent):
        message = obj.message
    elif isinstance(obj, Message):
        message = obj
    else:
        raise TypeError('The argument must be an instance of either MessageEvent or Message.')
    
    for seg in message:
        msg_type = seg.type
        if msg_type == 'text':
            message_str += seg.data['text']
        elif msg_type == 'face':
            face_id = str(seg.data['id'])
            if desc := faces.get(face_id, ''):
                message_str += f'[/{desc}]'
        elif msg_type == 'image':
            if desc_image:
                desc = await describe_image(seg.data['url'])
                if summary := seg.data['summary']:
                    message_str += f'[动画表情, details: {desc}]'
                else:
                    message_str += f'[图片, details: {desc}]'
            else:
                if summary := seg.data['summary']:
                    message_str += summary
                else:
                    message_str += f'[图片]'
        elif msg_type == 'at':
            message_str += f"@{seg.data['qq']}"
        else:
            message_str += str(seg)

    if isinstance(obj, MessageEvent):
        if obj.is_tome():
            message_str = f'@{self_name} {message_str}'
        if obj.reply:
            reply_content = obj.reply.message.extract_plain_text()
            if not reply_content:
                reply_content = ['图片']
            message_str = f'(回复{obj.reply.sender.user_id}“{reply_content}”)' + message_str

    return message_str



async def get_random_picture(path: Path) -> Path | None:
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a valid directory.")

    files = [file for file in path.iterdir() if file.is_file()]
    if not files:
        return None
    return random.choice(files)
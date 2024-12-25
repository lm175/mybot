from nonebot.adapters.onebot.v11 import MessageEvent, Message
from httpx import AsyncClient

from datetime import datetime
from pathlib import Path
import random

from .base import ChatBotMessage, UserData, BaseBot
from .model import glmbot, qwenbot
from .config import config

default_identity = config.chat_default_identity


async def seprate_message(message: Message) -> tuple[str, list[bytes]]:
    """
    提取Message中的文本和图片
    """
    images: list[bytes] = []
    text: str = ""
    for seg in message:
        msgtype = seg.type
        if msgtype == "image":
            text += str(seg)
            async with AsyncClient() as cli:
                res = await cli.get(seg.data["url"])
                images.append(res.content)
        else:
            text += str(seg)
    return text, images


async def handle_message(event: MessageEvent) -> ChatBotMessage:
    """
    将Event转化为ChatBotMessage类，可直接调用BaseBot类的方法
    """
    message = event.get_message()
    user_id = event.get_user_id()
    text, images = await seprate_message(message)

    if event.reply: # 引用消息处理
        replytext, replyimages = await seprate_message(event.reply.message)
        text = replytext + text
        for img in replyimages:
            images.append(img)

    try:    # 获取用户昵称
        user_nickname = event.sender.nickname
        text = f'用户“{user_nickname}”对你说：' + text
    except:
        pass

    formatted_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = f'[现在时间 {formatted_now}]\n' + text

    user = UserData(user_id)
    identity = user.identity
    if identity == "default":
        identity = default_identity
    chatmsg = ChatBotMessage(identity + text, images, user)

    return chatmsg


def get_chat_bot(user_id: str) -> BaseBot:
    """
    根据用户当前的模型返回BaseBot对象
    """
    user = UserData(user_id)
    current_model = user.current_model
    if current_model == "chatglm":
        chatbot = glmbot
    elif current_model == "通义千问":
        chatbot = qwenbot
    return chatbot



async def get_random_picture(path: Path) -> Path | None:
    if not path.is_dir():
        raise NotADirectoryError(f"{path} is not a valid directory.")

    files = [file for file in path.iterdir() if file.is_file()]
    if not files:
        return None
    return random.choice(files)
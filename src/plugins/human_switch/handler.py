from dataclasses import dataclass

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment
)
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .config import config



@dataclass
class Session:
    message_id: int
    user_id: int
    group_id: int = 0

sessions: dict[int, Session] = {}


hunman_switch = on_command("转人工", priority=5, block=True)

@hunman_switch.handle()
async def _(bot: Bot, event: MessageEvent, msg: Message = CommandArg()):
    if not msg:
        await hunman_switch.finish("请在指令后添加需要转发的内容")
    
    if isinstance(event, GroupMessageEvent):
        session_id = (await bot.send_private_msg(
            user_id=config.admin_id,
            message=f"来自群{event.group_id}用户{event.user_id}的消息：\n{msg}"
        ))['message_id']
        sessions[session_id] = Session(message_id=event.message_id, user_id=event.user_id, group_id=event.group_id)
    elif isinstance(event, PrivateMessageEvent):
        session_id = (await bot.send_private_msg(
            user_id=config.admin_id,
            message=f"来自用户{event.user_id}的消息：\n{msg}"
        ))['message_id']
        sessions[session_id] = Session(message_id=event.message_id, user_id=event.user_id)
    else:
        await hunman_switch.finish()
    
    await hunman_switch.finish("✅消息已转发")



async def session_checker(event: MessageEvent) -> bool:
    if event.reply and event.reply.message_id in sessions:
        return True
    return False

admin_reply = on_message(rule=session_checker, permission=SUPERUSER, priority=5, block=True)

@admin_reply.handle()
async def _(bot: Bot, event: MessageEvent):
    session = sessions.get(event.reply.message_id) # type: ignore
    if not session:
        return
    msg = MessageSegment.reply(session.message_id) + f"收到回复:\n" + event.message
    if session.group_id:
        await bot.send_group_msg(group_id=session.group_id,message=msg)
    else:
        await bot.send_private_msg(user_id=session.user_id, message=msg)
    
    sessions.pop(event.reply.message_id) # type: ignore
    await admin_reply.finish("✅已回复用户")

from nonebot import on_notice, on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent, GroupIncreaseNoticeEvent
from nonebot.adapters.onebot.v11.helpers import extract_image_urls
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .data import GroupWelcomData


from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="群聊管理",
    description="群聊管理插件",
    usage=(
        "设置入群欢迎\n"
        "   介绍：设置入群欢迎词，可加图片\n"
        " \n"
        "（待完善）"
    ),
    extra={
        "notice": "仅群主/管理员可用"
    }
)



async def INCchecker(event: GroupIncreaseNoticeEvent) -> bool:
    return True

inc = on_notice(rule=INCchecker)

@inc.handle()
async def _(event: GroupIncreaseNoticeEvent):
    group_id = str(event.group_id)
    user_id = event.user_id
    if user_id == event.self_id:
        pass
    else:
        message = MessageSegment.at(user_id)
        welcom_data = GroupWelcomData(group_id)
        message += await welcom_data.get_welcom_msg()
        await inc.send(message)



# 设置入群欢迎
set_welcom = on_command(
    "设置入群欢迎",
    permission=GROUP_ADMIN | GROUP_OWNER | SUPERUSER,
    priority=20,
    block=True
)

@set_welcom.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg:
        state["welcome_msg"] = arg

@set_welcom.got("welcome_msg", prompt="请发送欢迎消息")
async def _(state: T_State, event: GroupMessageEvent):
    message: Message = state["welcome_msg"]
    text = message.extract_plain_text()
    images = extract_image_urls(message)

    welcom_data = GroupWelcomData(str(event.group_id))
    await welcom_data.set_group_welcom(text=text, images=images)
    rep = MessageSegment.text("已将本群入群欢迎修改为:\n") + message
    await set_welcom.finish(rep)
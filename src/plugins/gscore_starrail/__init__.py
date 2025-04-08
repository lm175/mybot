from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..GenshinUID import handle_message
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="星穹铁道",
    description="全功能星穹铁道插件",
    usage=(
        "发送“sr帮助”查看功能列表"
    ),
)

srcmd = on_command(
    "sr",
    aliases={"崩铁", "星铁", "星穹铁道"},
    priority=1, block=True
)

@srcmd.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not event.is_tome():
        return
    if cmd := args.extract_plain_text():
        event.message = event.original_message= Message(f'sr{cmd}')
        await handle_message(bot, event)
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..GenshinUID import handle_message
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="鸣潮",
    description="全功能鸣潮查询插件",
    usage=(
        "发送“ww帮助”查看功能列表"
    ),
)


wwcmd = on_command(
    "ww",
    aliases={"WW", "鸣潮", "库洛"},
    priority=1, block=True
)

@wwcmd.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if cmd := args.extract_plain_text():
        event.message = event.original_message = Message(f'ww{cmd}')
        await handle_message(bot, event)
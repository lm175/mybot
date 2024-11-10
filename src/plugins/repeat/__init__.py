import asyncio
from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="复读机",
    description="自动复读群消息",
    usage="一分钟内连续出现两条相同消息时触发"
)


last_messages = {}
last_repeat_messages = {}

follow_repeat = on_message(priority=100)

@follow_repeat.handle()
async def handle_first_receive(event: GroupMessageEvent):
    group_id = event.group_id
    message = event.get_message()

    text = str(message)
    for k in ['人品', '原神']:
        if k in text:
            return

    if group_id not in last_messages:
        last_messages[group_id] = message
    else:
        if last_messages[group_id] == message:
            # 检查这次消息内容是否与上次跟读的内容相同
            if group_id in last_repeat_messages and last_repeat_messages[group_id] == message:
                return
            else:
                last_repeat_messages[group_id] = message
                last_messages[group_id] = ""  # 避免连续触发
                await follow_repeat.send(message)
        else:
            last_messages[group_id] = message

    asyncio.create_task(clear_last_message(group_id))


async def clear_last_message(group_id):
    await asyncio.sleep(60)
    if group_id in last_messages:
        last_messages[group_id] = ""


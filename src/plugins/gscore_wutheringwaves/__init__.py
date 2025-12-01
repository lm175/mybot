from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

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




from .handler import next_tower, next_slash

# from .tower import generate_tower_images, get_period_data, get_period_id
# from nonebot import require
# require("nonebot_plugin_localstore")
# import nonebot_plugin_localstore as store

# next_tower = on_command("ww下期深塔", priority=1, block=True)

# @next_tower.handle()
# async def _():
#     current_period_id = await get_period_id()
#     next_period_id = str(int(current_period_id) + 1)

#     # 尝试从本地获取下一期深塔图片
#     data_dir = store.get_plugin_data_dir()
#     tower_dir = data_dir / "tower" / next_period_id
#     if tower_dir.exists() and any(tower_dir.iterdir()):
#         pics = []
#         for img_file in sorted(tower_dir.iterdir()):
#             with open(img_file, 'rb') as f:
#                 pics.append(f.read())
#         next_period_data = await get_period_data(next_period_id)
#     else:
#         # 本地无图片，生成新图片
#         pics = await generate_tower_images(next_period_id)
#         next_period_data = await get_period_data(next_period_id)
#         # 保存图片到本地
#         tower_dir.mkdir(parents=True, exist_ok=True)
#         for idx, pic in enumerate(pics):
#             with open(tower_dir / f"area_{idx+1}.png", 'wb') as f:
#                 f.write(pic)


#     msg = Message(MessageSegment.node_custom(
#         user_id=2854196310,
#         nickname="小助手",
#         content=f"深塔第{next_period_id}期\n" +
#                 f"开放时间：{next_period_data.begin_dt} 至 {next_period_data.end_dt}"
#     ))

#     for pic in pics:
#         msg.append(MessageSegment.node_custom(
#             user_id=2854196310,
#             nickname="小助手",
#             content=Message(MessageSegment.image(pic))
#         ))
    
#     msg.append(MessageSegment.node_custom(
#         user_id=2854196310,
#         nickname="小助手",
#         content="数据来源：https://ww2.hakush.in/"
#     ))
#     await next_tower.send(msg)



# delete_images_cmd = on_command("ww删除深塔图片", priority=1, block=True, permission=SUPERUSER)
# @delete_images_cmd.handle()
# async def _(args: Message = CommandArg()):
#     data_dir = store.get_plugin_data_dir()
#     target_dir = data_dir / "tower" / args.extract_plain_text().strip()
#     if target_dir.exists():
#         for img_file in target_dir.iterdir():
#             img_file.unlink()
#         target_dir.rmdir()
#         await delete_images_cmd.finish(f"已删除深塔图片，路径：{target_dir}")
#     else:
#         await delete_images_cmd.finish(f"未找到指定路径的深塔图片：{target_dir}")
    

# from .slash import generate_slash_images, get_period_id as get_slash_period_id

# next_slash = on_command("ww下期海墟", priority=1, block=True)

# @next_slash.handle()
# async def _():
#     current_period_id = await get_slash_period_id()
#     next_period_id = str(int(current_period_id) + 1)

#     pics = await generate_slash_images(next_period_id)

#     msg = Message()
#     for pic in pics:
#         msg.append(MessageSegment.node_custom(
#             user_id=2854196310,
#             nickname="小助手",
#             content=Message(MessageSegment.image(pic))
#         ))
#     msg.append(MessageSegment.node_custom(
#         user_id=2854196310,
#         nickname="小助手",
#         content="数据来源：https://ww2.hakush.in/"
#     ))
#     await next_slash.send(msg)
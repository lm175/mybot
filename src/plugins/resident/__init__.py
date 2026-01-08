from nonebot import on_request, on_notice
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent, FriendRequestEvent
from nonebot import require, get_bot
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

import random, asyncio

from .group_invite import *

# 自动回赞
like_me = on_notice()

@like_me.handle()
async def _(bot: Bot, event: NoticeEvent):
    event_data = event.__dict__
    if event_data.get("sub_type") == "profile_like":
        await bot.send_like(user_id=event_data["operator_id"], times=10)



# 自动同意好友
friend_request = on_request(priority=5, block=False)

@friend_request.handle()
async def _(bot: Bot, event: FriendRequestEvent):
    await bot.set_friend_add_request(flag=event.flag, approve=True)



# 自动点赞
###



# key签到
@scheduler.scheduled_job(
    trigger="cron",
    hour=0,          # 小时：0 点（24小时制）
    minute=1,        # 分钟：0 分（可选，默认 0，显式指定更清晰）
    id="daily_midnight_job",  # 任务唯一ID（必填，用于后续管理任务）
)
async def daily_midnight_task():
    try:
        bot: Bot = get_bot() # type: ignore
        await asyncio.sleep(random.randint(0, 300))  # 随机延迟0-5分钟
        await bot.send_private_msg(
            user_id=3889050520,
            message=Message("key签到")
        )
    except Exception as e:
        print(f"发送消息失败：{e}")
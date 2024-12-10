from nonebot import on_request, on_notice
from nonebot.adapters.onebot.v11 import Bot, NoticeEvent, FriendRequestEvent

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
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from nonebot import get_bot
from nonebot.log import logger
from typing import List, Dict, Any


@scheduler.scheduled_job("cron", hour=0, minute=0, id="sendlike")
async def _():
    bot = get_bot()
    users: List[int] = []
    try:    # 获取好友列表
        friend_infos: List[Dict[str, Any]] = await bot.call_api("get_friend_list")
        friend_ids: List[int] = [f["user_id"] for f in friend_infos if f["user_id"] != int(bot.self_id)]
        users.extend(friend_ids)
    except Exception as e:
        logger.error(e)
 #   try:    # 获取点赞列表
 #       profile_like = await bot.call_api("get_profile_like")
 #       user_infos: List[Dict[str, Any]] = profile_like["userInfos"]
 #       for user in user_infos:
 #           if user["uin"] not in users:
 #               users.append(user["uin"])
 #   except Exception as e:
 #       logger.error(e)
    
    for u in users: # 点赞
        try:
            await bot.call_api("send_like", user_id=u, times=10)
        except:
            pass

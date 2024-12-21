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

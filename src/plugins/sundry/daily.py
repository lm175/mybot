from nonebot import on_fullmatch, on_keyword
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment

send_like_records = []
fortune_records = {}

# 检查是否已经点过赞
async def check_and_mark_command(user_id: int) -> bool:
    global send_like_records
    if user_id in send_like_records:
        return False  # 已经赞过了
    send_like_records.append(user_id)  # 标记为已点赞
    return True


Sendlike = on_fullmatch(('赞我', '点赞'), priority=5, block=True)

@Sendlike.handle()
async def handle_send_likes(bot: Bot, event: MessageEvent):
    user_id = event.user_id

    # if await check_and_mark_command(user_id):
    #     await bot.send_like(user_id=user_id, times=10)
    #     await Sendlike.finish('给你点了10个赞，记得先加好友哦', at_sender=True)

    # await Sendlike.finish('今天已经点过赞了哦，请明天再来吧', at_sender=True)
    try:
        await bot.send_like(user_id=user_id, times=10)
        await Sendlike.finish('给你点了10个赞，加好友后会自动点赞哦', at_sender=True)
    except:
        await Sendlike.finish('今天已经点过赞了哦，请明天再来吧', at_sender=True)





async def check_fortune_records(user_id: str):
    if user_id in fortune_records:
        return fortune_records[user_id], "cache"
    return "https://www.hhlqilongzhu.cn/api/tu_yunshi.php", "url"


fortune = on_keyword({"今日运势"}, priority=10)

@fortune.handle()
async def _(bot: Bot, event: MessageEvent):
    user_id = event.get_user_id()
    image, method = await check_fortune_records(user_id)
    res = await fortune.send(MessageSegment.image(image), at_sender=True)

    if method == "url":
        message_id = res["message_id"]
        data = await bot.call_api("get_msg", message_id=message_id)
        img_url = [a["data"]["url"] for a in data["message"] if a["type"] == "image"][0]
        fortune_records[user_id] = img_url



from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

@scheduler.scheduled_job("cron", hour=0, minute=0, id="clean_sundry_records")
async def clean_sundry_records():
    global send_like_records, fortune_records
    send_like_records = []
    fortune_records = {}


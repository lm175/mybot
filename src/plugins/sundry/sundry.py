import asyncio, json, random
from nonebot.rule import to_me
from nonebot import on_command, on_keyword, on_message, on_fullmatch, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    MessageEvent,
    GroupMessageEvent,
    PokeNotifyEvent,
    Message,
    MessageSegment
)
from nonebot.typing import T_State
from nonebot.params import ArgStr, CommandArg
from httpx import AsyncClient




async def group_checker(event: GroupMessageEvent) -> bool:
    return event.group_id == 938723856


zbsbqb = on_keyword({'这是表情包'}, rule=group_checker)
@zbsbqb.handle()
async def _():
    await zbsbqb.send('这不是表情包')





# async def at_with_no_message(event: GroupMessageEvent) -> bool:
#     message = str(event.get_message())
#     return not message

# only_at_bot = on_message(rule=to_me()&at_with_no_message, priority=10)

# @only_at_bot.handle()
# async def _():
#     await only_at_bot.send('你干嘛', at_sender=True)



cd_list = []
wife = on_fullmatch("今日老婆", priority=10)
@wife.handle()
async def handle_wife(event: MessageEvent):
    user_id = event.user_id
    if user_id in cd_list:
        await wife.finish("欸？(,,Ծ‸Ծ,, )你才刚刚结婚不久吧？")
    cd_list.append(user_id)
    asyncio.create_task(remove_id(user_id))
    url = "https://api.cenguigui.cn/api/pic/?type=iphone"
    reply = "你今天的老婆是她哦" + MessageSegment.image(url)
    await wife.finish(reply, at_sender=True)

async def remove_id(user_id):
    await asyncio.sleep(60)
    cd_list.remove(user_id)



abstract = on_command("raw", priority=5, block=True)

@abstract.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if arg.extract_plain_text().strip():
        state["abstract"] = arg.extract_plain_text().strip()


@abstract.got("abstract", prompt="你想显示什么消息的源码？")
async def _(event: Event, target_text: str = ArgStr("abstract")):
    target_text += str(event.get_event_description())
    if ',type=sticker' in str(event.get_message()):
        await abstract.send('大表情')
    await abstract.send(target_text, at_sender=True)




kfc = on_fullmatch("疯狂星期四", priority=15)
@kfc.handle()
async def handle_kfc_text():
    url = "https://www.hhlqilongzhu.cn/api/yl_kfc.php"
    async with AsyncClient() as client:
        res = await client.get(url)
    await kfc.send(res.text)




fabing = on_command("发病", priority=10, block=True)
@fabing.handle()
async def handle_ill(bot: Bot, event: MessageEvent, arg: Message=CommandArg()):
    target_id = 0
    for seg in event.get_message():
        if seg.type == "at":
            target_id = seg.data["qq"]
            break
    if target_id:
        user_info = await bot.get_stranger_info(user_id=target_id)
        target_name = user_info["nick"]
    elif arg:
        target_name = arg.extract_plain_text()
    else:
        await fabing.finish("你还没有指定发病对象呢")
    
    url = "https://api.lolimi.cn/API/fabing/fb.php"
    data = {"name": target_name, "type": "json"}
    try:
        async with AsyncClient() as client:
            res = await client.get(url=url, params=data)
            text = json.loads(res.text)["data"]
    except Exception as e:
        text = str(e)
    await fabing.send(text)



pokeme = on_notice()

@pokeme.handle()
async def _(bot: Bot, event: PokeNotifyEvent):
    if event.target_id == event.self_id:
        image_url = [
            "https://gxh.vip.qq.com/club/item/parcel/item/86/86d5aa7bbc9bf354208210b8c5ad6e1b/raw300.gif",
            "https://gxh.vip.qq.com/club/item/parcel/item/ce/cebe76e218356b2488bcae5c9075b924/raw300.gif",
            "https://gxh.vip.qq.com/club/item/parcel/item/85/8580111d6dff1d4efea33635547c5140/raw300.gif"
        ]
        reply_list = [
            MessageSegment.image(random.choice(image_url)),
            "...嗯？（・∀・）",
            "不要再戳桃子啦QwQ",
            "๐(´,,•ω•,,｀)？",
            "反击！( ง `ω´ )۶"
        ]
        msg = random.choice(reply_list)
        if msg == "反击！( ง `ω´ )۶":
            times = random.choices([1, 3], [4, 1], k=1)[0]
            if times == 3:
                msg = "“ψ(｀∇´)ψ 木大木大木大木大木大！"
            await pokeme.send(msg)
            if event.group_id:
                for _ in range(times):
                    await bot.call_api("group_poke", group_id=event.group_id, user_id=event.user_id)
                    await asyncio.sleep(0.1)
            else:
                for _ in range(times):
                    await bot.call_api("friend_poke", user_id=event.user_id)
                    await asyncio.sleep(0.1)
        else:
            await pokeme.send(msg)

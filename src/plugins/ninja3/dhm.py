from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    PrivateMessageEvent
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText

import asyncio

from .utils import RedeemCode, UidData, DHM, QQ_TO_UID, FORBIDDEN
from .utils import load_from_json, save_to_json, load_from_txt, save_to_txt



async def use_driver_to_redeem(bot: Bot, notice_list: list[str], redeem: RedeemCode, data: UidData):
    tips = {}
    for qq in data.data:
        uid_list = data.get_users_uid(qq)
        images = []
        for uid in uid_list:
            tip_msg, img = await asyncio.to_thread(redeem.redeem_for_user, str(uid))
            while tip_msg == "领取失败，Internal Server Error":
                tip_msg, img = await asyncio.to_thread(redeem.redeem_for_user, str(uid))
            tips[uid] = tip_msg
            images.append(img)
        if qq in notice_list:
            uid_str = ""
            for u in uid_list:
                uid_str += f"\n{u}"
            message = MessageSegment.text(f"[{redeem.dhm}]{uid_str}\n已完成兑换\n")
            for img in images:
                message += MessageSegment.image(img)
            message += "发送 /关闭提醒 将不再接收该消息"
            await bot.send_private_msg(user_id=int(qq), message=message)

    return tips


async def creat_new_driver_to_redeem(bot, notice_list, dhm, data):
    redeem = await asyncio.to_thread(RedeemCode, dhm)
    return await use_driver_to_redeem(bot, notice_list, redeem, data)




dhm_update = on_command("更新兑换码", priority=10, block=True)


@dhm_update.handle()
async def handle_first_recieve(matcher: Matcher, dhm: Message = CommandArg()):
    if dhm.extract_plain_text():
        matcher.set_arg('dhm', dhm)

@dhm_update.got('dhm', prompt='请输入兑换码')
async def handle_update(bot: Bot, dhm: str = ArgPlainText('dhm')):
    text = load_from_txt(DHM)
    if text == dhm:
        await dhm_update.finish('这个兑换码已经更新过啦~')
    await dhm_update.send('检测中··')

    redeem = await asyncio.to_thread(RedeemCode, dhm)
    is_right_code = await asyncio.to_thread(redeem.dhm_checker)
    if is_right_code:
        save_to_txt(DHM, dhm)
        await dhm_update.send('更新成功！正在给已绑定的uid兑换，请耐心等待哦~')
    else:
        await dhm_update.finish('兑换码好像不太对呢，再检查一下吧')

    data = UidData(load_from_json(QQ_TO_UID))
    # 获取好友列表和禁用提醒名单
    friends = await bot.get_friend_list()
    friend_qq_list = [str(f.get('user_id')) for f in friends]
    forbidden_list = load_from_json(FORBIDDEN)
    notice_list = [qq for qq in friend_qq_list if qq not in forbidden_list]
    # 创建两个并发协程
    data0, data1 = data.split_list()
    results = await asyncio.gather(
        creat_new_driver_to_redeem(bot, notice_list, dhm, UidData(data0)),
        use_driver_to_redeem(bot, notice_list, redeem, UidData(data1))
    )

    msg = Message()
    for i in range(2):
        reply_text = f"[task_{i}]"
        for k, v in results[i].items():
            reply_text += f"\n{k}: {v}"
        msg += MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname="",
            content=reply_text
        )
    await dhm_update.send(msg)
    



remind_close = on_command('关闭提醒', priority=10, block=True)
remind_open = on_command('开启提醒', priority=10, block=True)

# 添加和取消提醒
@remind_close.handle()
async def _(event: PrivateMessageEvent):
    forbidden_list = load_from_json(FORBIDDEN)
    user_id = event.get_user_id()
    if user_id not in forbidden_list:
        forbidden_list.append(user_id)
        save_to_json(FORBIDDEN, forbidden_list)
    await remind_close.send("已关闭提醒\n如需开启请发送 /开启提醒")

@remind_open.handle()
async def _(event: PrivateMessageEvent):
    forbidden_list = load_from_json(FORBIDDEN)
    user_id = event.get_user_id()
    if user_id in forbidden_list:
        forbidden_list.remove(user_id)
        save_to_json(FORBIDDEN, forbidden_list)
    await remind_open.send('已开启提醒')

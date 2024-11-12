from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText

from sqlalchemy import select

import asyncio
from datetime import date

from .utils import RedeemCode, get_current_uids, split_list, update_codes
from .database import Users, GiftCodes
from .requires import async_scoped_session



async def use_driver_to_redeem(bot: Bot, redeem: RedeemCode, users: list[Users], session: async_scoped_session):
    tips: dict[int, str] = {}
    for usr in users:
        game_ids = await get_current_uids(session, usr.user_id)
        images = []
        for uid in game_ids:
            tip_msg, img = await asyncio.to_thread(redeem.redeem_for_user, str(uid))
            tips[uid] = tip_msg
            images.append(img)
        if usr.need_remind: # 发送提醒消息
            uid_str = ""
            for u in game_ids:
                uid_str += f"\n{u}"
            message = MessageSegment.text(f"[{redeem.code}]{uid_str}\n已完成兑换\n")
            for img in images:
                message += MessageSegment.image(img)
            message += "发送 /关闭提醒 将不再接收该消息"
            await bot.send_private_msg(user_id=usr.user_id, message=message)

    return tips


async def creat_new_driver_to_redeem(bot: Bot, code: str, users: list[Users], session: async_scoped_session):
    redeem = await asyncio.to_thread(RedeemCode, code)
    return await use_driver_to_redeem(bot, redeem, users, session)




dhm_update = on_command("更新兑换码", aliases={"更新礼包码"}, priority=10, block=True)


@dhm_update.handle()
async def handle_first_recieve(matcher: Matcher, code: Message = CommandArg()):
    if code.extract_plain_text():
        matcher.set_arg('code', code)

@dhm_update.got('code', prompt='请输入兑换码')
async def handle_update(bot: Bot, session: async_scoped_session, code: str = ArgPlainText('code')):
    if giftCodes := await session.get(GiftCodes, code):
        await dhm_update.finish('这个兑换码已经更新过啦~')

    await dhm_update.send('检测中··')
    redeem = await asyncio.to_thread(RedeemCode, code)
    is_right_code = await asyncio.to_thread(redeem.dhm_checker)
    if is_right_code:
        session.add(GiftCodes(code=code, time=date.today(), available=True))
        await update_codes(session)
        await dhm_update.send('更新成功！正在给已绑定的uid兑换，请耐心等待哦~')
    else:
        await dhm_update.finish('兑换码好像不太对呢，再检查一下吧')

    res = await session.scalars(select(Users))
    allusers = res.all()
    users = split_list(allusers)
    # 创建两个并发协程
    results = await asyncio.gather(
        use_driver_to_redeem(bot, redeem, users[0], session),
        creat_new_driver_to_redeem(bot, code,  users[1], session)
    )

    msg = Message()
    for i in range(2):
        text = f"[task_{i}]"
        for k, v in results[i].items():
            text += f"\n{k}: {v}"
        msg += MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname="桃子",
            content=text
        )
    await session.commit()
    await dhm_update.finish(msg)
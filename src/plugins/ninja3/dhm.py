from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText

import asyncio
from datetime import date

from aiosqlite import Row

from .utils import RedeemCode, split_list
from .database import db_instance as db


async def use_driver_to_redeem(
        bot: Bot,
        redeem: RedeemCode,
        users: list[Row],
    ):
    tips: dict[int, str] = {}
    friends = await bot.get_friend_list()
    friend_list = [str(f.get('user_id')) for f in friends]
    for usr in users:
        game_ids = await db.get_user_uids(usr[0])
        images = []
        for uid in game_ids:
            tip_msg, img = await asyncio.to_thread(
                redeem.redeem_for_user,
                str(uid)
            )
            tips[uid] = tip_msg
            images.append(img)
        if usr[2]: # 发送提醒消息
            if str(usr[0]) in friend_list:
                uid_str = ""
                for u in game_ids:
                    uid_str += f"\n{u}"
                message = MessageSegment.text(
                    f"[{redeem.code}]{uid_str}\n已完成兑换\n"
                )
                for img in images:
                    message += MessageSegment.image(img)
                message += "发送 /关闭提醒 将不再接收该消息"
                await bot.send_private_msg(
                    user_id=usr[0], 
                    message=message
                )

    return tips


async def creat_new_driver_to_redeem(
        bot: Bot,
        code: str,
        users: list[Row],
    ):
    redeem = await asyncio.to_thread(RedeemCode, code)
    return await use_driver_to_redeem(bot, redeem, users)




dhm_update = on_command("更新兑换码", aliases={"更新礼包码"}, priority=10, block=True)


@dhm_update.handle()
async def _(matcher: Matcher, code: Message = CommandArg()):
    if code.extract_plain_text():
        matcher.set_arg('code', code)

@dhm_update.got('code', prompt='请输入兑换码')
async def _(bot: Bot, code: str = ArgPlainText('code')):
    if await db.code_exists(code):
        await dhm_update.finish('这个兑换码已经更新过啦~')

    await dhm_update.send('检测中··')
    redeem = await asyncio.to_thread(RedeemCode, code)
    is_right_code = await asyncio.to_thread(redeem.dhm_checker)
    if is_right_code:
        await db.code_add(code=code, time=date.today(), available=True)
        await db.codes_update()
        await dhm_update.send('更新成功！正在给已绑定的uid兑换，请耐心等待哦~')
    else:
        await dhm_update.finish('兑换码好像不太对呢，再检查一下吧')

    allusers = await db.get_users()
    users = split_list(allusers)
    # 创建两个并发协程
    results = await asyncio.gather(
        use_driver_to_redeem(bot, redeem, users[0]),
        creat_new_driver_to_redeem(bot, code,  users[1])
    )

    msg = Message()
    for i in range(len(results)):
        text = f"[task_{i}]"
        for k, v in results[i].items():
            text += f"\n{k}: {v}"
        msg += MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname="桃子",
            content=text
        )
    await db.commit()
    await dhm_update.finish(msg)
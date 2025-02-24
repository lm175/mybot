from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText
from nonebot.log import logger

from datetime import date


from .utils import redeem_code, code_checker
from .db_manager import DatabaseManager as db




dhm_update = on_command("更新兑换码", aliases={"更新礼包码"}, priority=10, block=True)


@dhm_update.handle()
async def _(matcher: Matcher, code: Message = CommandArg()):
    if code.extract_plain_text():
        matcher.set_arg('code', code)

@dhm_update.got('code', prompt='请输入兑换码')
async def _(bot: Bot, code: str = ArgPlainText('code')):
    code_exists = await db.query_one(
        "SELECT code FROM giftcodes WHERE code=? LIMIT 1",
        (code,)
    )
    if code_exists:
        await dhm_update.finish('这个兑换码已经更新过啦~')

    await dhm_update.send('检测中··')
    is_right_code = await code_checker(code)
    if is_right_code:
        await db.execute(
            "INSERT INTO giftcodes (code, time, available) VALUES (?, ?, ?)",
            (code, date.today(), True)
        )
        await dhm_update.send('更新成功！正在给已绑定的uid兑换，请耐心等待哦~')
    else:
        await dhm_update.finish('兑换码好像不太对呢，再检查一下吧')


    result: dict[int, str] = {}
    all_users = await db.query_all(
        "SELECT user_id, need_remind FROM users",
        ()
    )
    for user in all_users:
        user_id = user[0]
        game_ids = await db.get_user_uids(user_id)
        print(game_ids)
        tip_msg = f"[{code}]"
        for game_id in game_ids:
            res = await redeem_code(game_id, code)
            print(f"{game_id}::: {res.msg}")
            result[game_id] = res.msg
            tip_msg += f"\n{game_id}: {res.msg}"
        tip_msg += "\n发送 /关闭提醒 将不再接收该消息"
        friend_list = await bot.get_friend_list()
        friend_user_ids = [f['user_id'] for f in friend_list]
        is_friend = user_id in friend_user_ids
        if game_ids and is_friend and user[1]:
            try:
                await bot.send_private_msg(
                    user_id=user_id,
                    message=tip_msg
                )
            except Exception as e:
                logger.warning(e)

    superusers = list(get_driver().config.superusers)
    superuser = superusers[0] if superusers else ""
    selfnames = list(get_driver().config.nickname)
    selfname = selfnames[0] if selfnames else "桃子"

    text = '```'
    for game_id, tip in result.items():
        text += f'\n{game_id}: {tip}'
    text += '```'

    msg = Message(MessageSegment.node_custom(
        user_id=int(bot.self_id),
        nickname=selfname,
        content=Message(MessageSegment.node_custom(
            user_id=int(bot.self_id),
            nickname=selfname,
            content=Message(MessageSegment(
                type="markdown",
                data={
                    "content": text
                }
            ))
        ))
    ))

    try:
        await dhm_update.send(msg)
    except Exception as e:
        logger.error(e)

    try:
        await bot.send_private_msg(
            user_id=int(superuser),
            message=msg
        )
    except Exception as e:
        logger.error(e)
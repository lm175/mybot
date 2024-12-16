from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    MessageEvent,
    PrivateMessageEvent
)
from nonebot.params import CommandArg, ArgStr
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.helpers import (
    extract_numbers,
    convert_chinese_to_bool
)

from .database import db_instance as db
from .utils import serch_uid, RedeemCode

import asyncio


uid_add = on_command(
    "忍3绑定uid",
    aliases={"忍三绑定uid", "忍3绑定UID", "忍三绑定UID"},
    priority=10,
    block=True
)


@uid_add.handle()
async def _(event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    user_id = event.user_id
    await db.get_user_info(user_id)
    if user := await db.get_user_info(user_id):
        if user[1] >= 5:
            await uid_add.finish("您绑定的uid数量已达上限")
    
    state['user_id'] = user_id
    if nums := extract_numbers(arg):
        state['game_id'] = int(nums[0])


@uid_add.got('game_id', prompt="请发送要绑定的uid")
async def _(state: T_State, game_id = ArgStr('game_id')):

    if len(game_id) != 9 and len(game_id) != 12:
        await uid_add.finish("欸？应该是9或12位才对吧？")
    game_id = int(game_id)
    uid_info = await serch_uid(game_id)
    if not uid_info:
        await uid_add.finish("这个uid好像不太对哦")

    if gameID := await db.get_gameid_info(game_id):
        await uid_add.finish(f"{game_id}已经被{gameID[1]}绑定过啦~")

    state['game_id'] = game_id
    await uid_add.send("玩家信息:\n" + uid_info + "\n是否确认？")


@uid_add.receive()
async def _(event: MessageEvent, state: T_State):
    msg = event.get_message()
    if convert_chinese_to_bool(msg):
        user_id: int = state['user_id']
        game_id: int = state['game_id']

        user = await db.get_user_info(user_id)
        if not user:
            await db.user_add(user_id, 0, True)

        await db.gameid_add(game_id, user_id)

        uids = await db.get_user_uids(user_id)
        uid_str = ""
        for u in uids:
            uid_str += f"\n{u}"
        await uid_add.send(f"添加成功，当前已绑定uid:{uid_str}\n正在检查可用的兑换码··")

        if codes := await db.get_available_codes():
            redeem = await asyncio.to_thread(RedeemCode, codes[0])
            reply_msg = Message()
            for c in codes:
                redeem.code = c
                _, img = await asyncio.to_thread(redeem.redeem_for_user, str(game_id))
                reply_msg += MessageSegment.text(c) + MessageSegment.image(img)
            await uid_add.send(reply_msg, at_sender=True)
            
        await db.user_update(user_id)
    else:
        await uid_add.send("已取消")





uid_del = on_command("忍3解除绑定", aliases={"忍三解除绑定"}, priority=10, block=True)


@uid_del.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    user_id = event.user_id
    user = await db.get_user_info(user_id)
    if not user:
        await uid_del.finish("你还没有绑定过uid呢")
    
    if nums := extract_numbers(arg):
        for n in nums:
            msg = await _handle_del_uid(user_id, int(n))
        await uid_del.finish(msg)
    else:
        uids = await db.get_user_uids(user_id)
        uid_str = ""
        for u in uids:
            uid_str += f"\n{u}"
        await uid_del.send(f"请发送要删除的uid: {uid_str}")


@uid_del.receive()
async def _(event: MessageEvent):
    if nums := extract_numbers(event.get_message()):
        user_id = event.user_id
        msg = await _handle_del_uid(user_id, int(nums[0]))
        await uid_del.finish(msg)
    await uid_del.finish("已退出当前操作")



async def _handle_del_uid(user_id: int, game_id: int) -> str:
    user = await db.get_user_info(user_id)
    gameID = await db.get_gameid_info(game_id)
    if user and gameID:
        if gameID[1] == user[0]:
            await db.gameid_del(game_id)
            await db.user_update(user_id)

            uids = await db.get_user_uids(user_id)
            uid_str = ""
            for u in uids:
                uid_str += f"\n{u}"
            return f"删除成功，当前已绑定uid:{uid_str}"

    return "你没有绑定过这个uid哦"






remind_close = on_command('关闭提醒', priority=10, block=True)
remind_open = on_command('开启提醒', priority=10, block=True)

# 添加和取消提醒
@remind_close.handle()
async def _(event: PrivateMessageEvent):
    if await db.get_user_info(event.user_id):
        await db.user_remind(event.user_id, False)
        await remind_close.send("已关闭提醒\n如需开启请发送 /开启提醒")

@remind_open.handle()
async def _(event: PrivateMessageEvent):
    if await db.get_user_info(event.user_id):
        await db.user_remind(event.user_id, True)
        await remind_open.send('已开启提醒')



uid_search = on_command("uid查询", priority=10, block=True)


@uid_search.handle()
async def handle_search_uid(arg: Message = CommandArg()):
    nums = extract_numbers(arg)
    if not nums:
        return
    uid = int(nums[0])
    user_info = await serch_uid(uid)
    await uid_search.finish(str(user_info))
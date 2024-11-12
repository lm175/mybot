from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg, ArgStr
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.helpers import extract_numbers, convert_chinese_to_bool

from .database import GameIDs, Users, GiftCodes
from .utils import serch_uid, get_current_uids, RedeemCode
from .requires import async_scoped_session
from sqlalchemy import select

import asyncio
from io import BytesIO

uid_add = on_command("忍3绑定uid", aliases={"忍三绑定uid", "忍3绑定UID", "忍三绑定UID"}, priority=10, block=True)


@uid_add.handle()
async def _(event: MessageEvent, session: async_scoped_session, state: T_State, arg: Message = CommandArg()):
    user_id = event.user_id
    if user := await session.get(Users, user_id):
        if user.uid_nums >= 5:
            await uid_add.finish("您绑定的uid数量已达上限")
    
    state['user_id'] = user_id
    if nums := extract_numbers(arg):
        state['game_id'] = int(nums[0])


@uid_add.got('game_id', prompt="请发送要绑定的uid")
async def _(state: T_State, session: async_scoped_session, game_id = ArgStr('game_id')):

    if len(game_id) != 9 and len(game_id) != 12:
        await uid_add.finish("欸？应该是9或12位才对吧？")
    game_id = int(game_id)
    uid_info = await serch_uid(game_id)
    if not uid_info:
        await uid_add.finish("这个uid好像不太对哦")

    if gameIDs := await session.get(GameIDs, game_id):
        await uid_add.finish(f"{game_id}已经被{gameIDs.user_id}绑定过啦~")

    state['game_id'] = game_id
    await uid_add.send("玩家信息:\n" + uid_info + "\n是否确认？")


@uid_add.receive()
async def _(event: MessageEvent, state: T_State, session: async_scoped_session):
    msg = event.get_message()
    if convert_chinese_to_bool(msg):
        user_id: int = state['user_id']
        game_id: int = state['game_id']

        user = await session.get(Users, user_id)
        if not user:
            user = Users(user_id=user_id, uid_nums=0, need_remind=True)
            session.add(user)
        user.uid_nums += 1

        gameID = GameIDs(game_id=game_id, user_id=user_id)
        session.add(gameID)

        uids = await get_current_uids(session, user_id)
        uid_str = ""
        for u in uids:
            uid_str += f"\n{u}"
        await uid_add.send(f"添加成功，当前已绑定uid:{uid_str}\n正在检查当前可用的兑换码··")

        if res := await session.scalars(select(GiftCodes.code).where(GiftCodes.available == True)):
            codes = res.all()
            redeem = await asyncio.to_thread(RedeemCode, codes[0])
            reply_msg = Message()
            for c in codes:
                redeem.code = c
                tip_msg, img = await asyncio.to_thread(redeem.redeem_for_user, str(game_id))
                reply_msg += MessageSegment.text(tip_msg) + MessageSegment.image(img)
            await uid_add.send(reply_msg, at_sender=True)
            
        await session.commit()
    else:
        await uid_add.send("已取消")





uid_del = on_command("忍3解除绑定", aliases={"忍三解除绑定"}, priority=10, block=True)


@uid_del.handle()
async def _(event: MessageEvent, session: async_scoped_session, arg: Message = CommandArg()):
    user_id = event.user_id
    user = await session.get(Users, user_id)
    if not user:
        await uid_del.finish("你还没有绑定过uid呢")
    
    if nums := extract_numbers(arg):
        for n in nums:
            msg = await _handle_del_uid(session, user_id, int(n))
        await session.commit()
        await uid_del.finish(msg)
    else:
        uids = await get_current_uids(session, user_id)
        uid_str = ""
        for u in uids:
            uid_str += f"\n{u}"
        await uid_del.send(f"请发送要删除的uid: {uid_str}")


@uid_del.receive()
async def _(event: MessageEvent, session: async_scoped_session):
    if nums := extract_numbers(event.get_message()):
        user_id = event.user_id
        msg = await _handle_del_uid(session, user_id, int(nums[0]))
        await session.commit()
        await uid_del.finish(msg)
    await uid_del.finish("已退出当前操作")



async def _handle_del_uid(session: async_scoped_session, user_id: int, game_id: int) -> str:
    user = await session.get(Users, user_id)
    gameID = await session.get(GameIDs, game_id)
    if user and gameID:
        if gameID.user_id == user.user_id:
            # user表
            user.uid_nums -= 1
            if not user.uid_nums:
                await session.delete(user)
            # uid表
            await session.delete(gameID)
            uids = await get_current_uids(session, user.user_id)

            uid_str = ""
            for u in uids:
                uid_str += f"\n{u}"
            return f"删除成功，当前已绑定uid:{uid_str}"

    return "你没有绑定过这个uid哦"






remind_close = on_command('关闭提醒', priority=10, block=True)
remind_open = on_command('开启提醒', priority=10, block=True)

# 添加和取消提醒
@remind_close.handle()
async def _(event: PrivateMessageEvent, session: async_scoped_session):
    if user := await session.get(Users, event.user_id):
        user.need_remind = False
        await session.commit()
        await remind_close.send("已关闭提醒\n如需开启请发送 /开启提醒")

@remind_open.handle()
async def _(event: PrivateMessageEvent, session: async_scoped_session):
    if user := await session.get(Users, event.user_id):
        user.need_remind = True
        await session.commit()
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
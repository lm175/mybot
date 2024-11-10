from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.params import CommandArg, ArgStr
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.helpers import extract_numbers, convert_chinese_to_bool

import json

from .utils import load_from_json
from .utils import UidData, QQ_TO_UID, serch_uid



uid_add = on_command("忍3绑定uid", aliases={"忍三绑定uid", "忍3绑定UID", "忍三绑定UID"}, priority=10, block=True)


@uid_add.handle()
async def handle_check_user(event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    qq = event.get_user_id()
    data = UidData(load_from_json(QQ_TO_UID))
    user_uid_list = data.get_users_uid(qq)
    if qq in user_uid_list and len(user_uid_list) >= 5:
        await uid_add.finish("您绑定的uid数量已达上限")
    
    state['data'] = data
    nums = extract_numbers(arg)
    if nums:
        state['uid'] = str(int(nums[0]))


@uid_add.got('uid', prompt="请发送要绑定的uid")
async def handle_check_uid(state: T_State, uid = ArgStr('uid')):

    if len(uid) != 9 and len(uid) != 12:
        await uid_add.finish("欸？应该是9或12位才对吧？")
    uid = int(uid)
    uid_info = await serch_uid(uid)
    if not uid_info:
        await uid_add.finish("这个uid好像不太对哦")

    data: UidData = state['data']
    all_uid_list = data.get_all_uids()
    if int(uid) in all_uid_list:
        qq = data.get_qq_from_uid(int(uid))
        await uid_add.finish(f"{uid}已经被{qq}绑定过啦~")

    await uid_add.send("玩家信息:\n" + uid_info + "\n是否确认？")


@uid_add.receive()
async def handle_uid_add(event: MessageEvent, uid = ArgStr('uid')):
    msg = event.get_message()
    if convert_chinese_to_bool(msg):
        qq = event.get_user_id()
        with open(QQ_TO_UID, 'r+', encoding='utf-8') as f:
            data = UidData(json.load(f))
            data.add_uid(qq, int(uid))
            f.seek(0)
            f.truncate()
            json.dump(data.data, f, ensure_ascii=False, indent=4)
        user_uid_list = data.get_users_uid(qq)
        uid_str = await _list_to_text(user_uid_list)
        await uid_add.finish(f"添加成功，当前已绑定uid:{uid_str}")
    else:
        await uid_add.send("已取消")





uid_del = on_command("忍3解除绑定", aliases={"忍三解除绑定"}, priority=10, block=True)


@uid_del.handle()
async def handle_user_check(event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    qq = event.get_user_id()
    data = UidData(load_from_json(QQ_TO_UID))
    if qq not in data.data:
        await uid_del.finish("你还没有绑定过uid呢")
    
    nums = extract_numbers(arg)
    user_uid_list = data.get_users_uid(qq)
    if nums:
        reply_text = await _handle_del_uid(qq, user_uid_list, nums)
        await uid_del.finish(reply_text)
    else:
        uid_str = await _list_to_text(user_uid_list)
        await uid_del.send(f"请发送要删除的uid: {uid_str}")
        state['user_uid_list'] = user_uid_list


@uid_del.receive()
async def handle_recieve_uid(event: MessageEvent, state: T_State):
    nums = extract_numbers(event.get_message())
    if not nums:
        await uid_del.finish("已退出当前操作")
    qq = event.get_user_id()
    user_uid_list = state['user_uid_list']
    reply_text = await _handle_del_uid(qq, user_uid_list, nums)
    await uid_del.send(reply_text)



async def _handle_del_uid(qq: str, user_uid_list: list[int], nums: list[float]) -> str:
    uid = int(nums[0])
    if uid in user_uid_list:
        with open(QQ_TO_UID, 'r+', encoding='utf-8') as f:
            data = UidData(json.load(f))
            data.del_uid(qq, uid)
            f.seek(0)
            f.truncate()
            json.dump(data.data, f, ensure_ascii=False, indent=4)
        uid_list_after_del = data.data.get(qq)
        uid_str = await _list_to_text(uid_list_after_del)
        return f"删除成功，当前已绑定uid:{uid_str}"
    else:
        return f"你没有绑定过这个uid哦"


async def _list_to_text(user_uid_list: list[int] | None) -> str:
    if not user_uid_list:
        return f"\n{user_uid_list}"
    uid_str = ""
    for uid in user_uid_list:
        uid_str += f"\n{uid}"
    return uid_str



uid_search = on_command("uid查询", priority=10, block=True)


@uid_search.handle()
async def handle_search_uid(arg: Message = CommandArg()):
    nums = extract_numbers(arg)
    if not nums:
        return
    uid = int(nums[0])
    user_info = await serch_uid(uid)
    await uid_search.finish(str(user_info))
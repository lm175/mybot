from nonebot import on_regex, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.adapters.onebot.v11.helpers import extract_numbers
from nonebot.rule import to_me
from nonebot.params import RegexGroup, CommandArg

from typing import Tuple

from .utils import load_from_json, save_to_json, serch_uid
from .requires import store
REMIND_PATH = store.get_plugin_data_file("remind.json")



boss = on_regex(r"(赤须|虎皮|金面|隼|蚊|青龙|红龙|双龙|蝙蝠|秃|剑|前台|猴|鸟|笔)", block=False, priority=10)
@boss.handle()
async def _(event: GroupMessageEvent, match: Tuple = RegexGroup()):
    data: dict[str, dict[str, list[int]]] = load_from_json(REMIND_PATH)
    group_id = str(event.group_id)
    boss_name = match[0]

    user_list = data[boss_name].get(group_id)
    numbers = extract_numbers(event.get_message())
    if user_list and numbers:
        flag = False # 检查是否存在正确uid
        for n in numbers:
            if 100000000 < int(n) < 999999999 and await serch_uid(int(n)):
                flag = True
        if flag:
            msg = event.get_message()
            for user in user_list:
                msg += " " +  MessageSegment.at(user_id=user)
            await boss.send(msg)



add_remind = on_regex(r"有(赤须|虎皮|金面|隼白|蚊子|青龙|红龙|双龙|蝙蝠|秃子|秃头|王剑|前台|猴子|鸟|毛笔)(喊|提醒|叫)我", rule=to_me(), priority=10)
@add_remind.handle()
async def _(event: GroupMessageEvent, match: Tuple = RegexGroup()):
    group_id = str(event.group_id)
    user_id = event.user_id
    boss_name = match[0]
    if boss_name == "隼白":
        boss_name = "隼"
    elif boss_name == "蚊子":
        boss_name = "蚊"
    elif boss_name == "王剑":
        boss_name = "剑"
    elif boss_name == "秃头":
        boss_name = "秃子"
    else:
        pass
    
    data: dict[str, dict[str, list[int]]] = load_from_json(REMIND_PATH)
    if group_id not in data[boss_name]:
        data[boss_name][group_id] = [user_id]
    else:
        if user_id not in data[boss_name][group_id]:
            data[boss_name][group_id].append(user_id)
    save_to_json(REMIND_PATH, data)

    await add_remind.send(f"添加成功，发</取消提醒 {boss_name}>可取消")



del_remind = on_command("取消提醒", aliases={"删除提醒"}, rule=to_me(), priority=10, block=True)
@del_remind.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    boss_name = args.extract_plain_text().strip()
    if boss_name == "隼白":
        boss_name = "隼"
    elif boss_name == "蚊子":
        boss_name = "蚊"
    elif boss_name == "王剑":
        boss_name = "剑"
    else:
        pass
    data: dict[str, dict[str, list[int]]] = load_from_json(REMIND_PATH)
    if boss_name in data:
        group_id = str(event.group_id)
        user_id = event.user_id
        user_list = data[boss_name].get(group_id)
        if user_list and user_id in user_list:
            data[boss_name][group_id].remove(user_id)
            save_to_json(REMIND_PATH, data)
            await del_remind.send(f"已删除<{boss_name}>的提醒任务")
    

from typing import Tuple, Any
import re
from nonebot.params import RegexGroup
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from datetime import timedelta, datetime
from nonebot import get_driver
from nonebot.rule import to_me
from nonebot import on_regex

from .setting import  reschedule_tasks, parse_function_call, load_from_json, path
from .test.model import chatbot

priority = 8



chinese_to_arabic = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18, '十九': 19,
    '二十': 20, '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25, '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29,
    '三十': 30, '三十一': 31, '三十二': 32, '三十三': 33, '三十四': 34, '三十五': 35, '三十六': 36, '三十七': 37, '三十八': 38, '三十九': 39,
    '四十': 40, '四十一': 41, '四十二': 42, '四十三': 43, '四十四': 44, '四十五': 45, '四十六': 46, '四十七': 47, '四十八': 48, '四十九': 49,
    '五十': 50, '五十一': 51, '五十二': 52, '五十三': 53, '五十四': 54, '五十五': 55, '五十六': 56, '五十七': 57, '五十八': 58, '五十九': 59,
    '六十': 60, '六十一': 61, '六十二': 62, '六十三': 63, '六十四': 64, '六十五': 65, '六十六': 66, '六十七': 67, '六十八': 68, '六十九': 69,
    '七十': 70, '七十一': 71, '七十二': 72, '七十三': 73, '七十四': 74, '七十五': 75, '七十六': 76, '七十七': 77, '七十八': 78, '七十九': 79,
    '八十': 80, '八十一': 81, '八十二': 82, '八十三': 83, '八十四': 84, '八十五': 85, '八十六': 86, '八十七': 87, '八十八': 88, '八十九': 89,
    '九十': 90, '九十一': 91, '九十二': 92, '九十三': 93, '九十四': 94, '九十五': 95, '九十六': 96, '九十七': 97, '九十八': 98, '九十九': 99,
    '一百': 100
}

remind_after = on_regex(
    r'([零一二两三四五六七八九十]+|\d+)个?(秒|分钟|小时|天|星期|周|月|年|世纪)[之以过]?后(提醒|喊|让|叫)我(.*?)$',
    priority=priority,
    rule=to_me()
)
remind_time = on_regex(
    r'(今|明)?天?(早|上|下|晚|中)?[午上]?([零一二两三四五六七八九十]+|\d+)(:|：|点钟?整?)零?([零一二三四五六七八九十]+|\d+|半|整|一刻)?分?(提醒|喊|让|叫)我(.*?)$',
    priority=priority,
    rule=to_me()
)

@remind_time.handle()
@remind_after.handle()
async def _(bot: Bot, event: MessageEvent, match: Tuple[Any,...] = RegexGroup()):
    # time_str = match[0]
    # if time_str.isdigit():
    #     time_number = int(match[0])
    # else:
    #     try:
    #         time_number = chinese_to_arabic[time_str]
    #     except:
    #         await remind_after.finish()

    # time_unit = match[1]
    # event_description: str = match[3]

    # # 计算提醒时间
    # if time_unit == "秒":
    #     delay = timedelta(seconds=time_number)
    # elif time_unit == "分钟":
    #     delay = timedelta(minutes=time_number)
    # elif time_unit == "小时":
    #     delay = timedelta(hours=time_number)
    # elif time_unit == "天":
    #     delay = timedelta(days=time_number)
    # elif time_unit == "周" or time_unit == "星期":
    #     delay = timedelta(weeks=time_number)
    # elif time_unit == "月":
    #     delay = timedelta(days=30 * time_number)
    # elif time_unit == "年":
    #     delay = timedelta(days=365 * time_number)
    # elif time_unit == "世纪":
    #     await remind_after.finish()
    # else:
    #     await remind_after.finish()
    messages = [{"role": "user", "content": event.message.extract_plain_text()}]
    tool_choice = {"type": "function", "function": {"name": "set_task"}}
    res = await chatbot.chat(messages, event.user_id, str(event.sender.nickname), tool_choice)
    while res.resp_type != "tool_calls":
        res = await chatbot.chat(messages, event.user_id, str(event.sender.nickname), tool_choice)

    msg = await parse_function_call(bot, event, messages, res)
    await remind_after.send(msg)
    




# @remind_time.handle()
# async def handle(bot: Bot, event: MessageEvent, match: Tuple[Any,...] = RegexGroup()):
#     day_st = match[0]
#     time_st = match[1]
#     hour_str = match[2]
#     minute_str = match[4]
#     event_description = match[6]

#     if re.match(r'^[零一二三四五六七八九十]+$', hour_str):
#         try:
#             hour = chinese_to_arabic[hour_str]
#         except:
#             await remind_time.finish()
#     else:
#         hour = int(hour_str)

#     if minute_str == "半":
#         minute = 30
#     elif minute_str == "整":
#         minute = 0
#     elif minute_str == "一刻":
#         minute = 15
#     elif isinstance(minute_str, str) and re.match(r'^[零一二三四五六七八九十]+$', minute_str):
#         try:
#             minute = chinese_to_arabic[minute_str]
#         except:
#             await remind_time.finish()
#     elif minute_str:
#         minute = int(minute_str)
#     else:
#         minute = 0

#     if isinstance(day_st, str):
#         if "明" in day_st:
#             day_add = 1
#         elif "后" in day_st:
#             day_add = 2
#         else:
#             day_add = 0
#     else:
#         day_add = 0
    
#     if isinstance(time_st, str):
#         if "晚" in time_st and 3 < hour <= 12:
#             hour += 12
#         if "中" in time_st and hour <= 3:
#             hour += 12
#         if "下" in time_st and hour <= 12:
#             hour += 12

#     if hour == 24:
#         hour = 0
#     if hour>24 or minute>60 or hour<0 or minute<0:
#         await remind_time.finish()

#     now = datetime.now()
#     target_time = datetime(now.year, now.month, now.day, hour, minute) + timedelta(days=day_add)

#     if target_time < now:
#         target_time += timedelta(days=1)
#     delay = target_time - now

#     reply_text = await set_remind(bot, event, event_description, delay)
#     await remind_time.finish(reply_text)

import json

cancel_remind = on_regex(r'((别|不要)(提醒|喊|叫)我?(.*?)了)|取消提醒', priority=priority, rule=to_me())

@cancel_remind.handle()
async def handle_cancel(bot: Bot, event: MessageEvent, match: Tuple[Any,...] = RegexGroup()):
    # task_id = match[0]
    # if not task_id:
    #     pass
    # user_id = event.user_id
    # msg = await cancel_(task_id, user_id)
    # await cancel_remind.send(msg)
    messages: list[dict] = []
    user_tasks: dict[str, list[dict[str, Any]]] = load_from_json(path)
    if event.get_user_id() not in user_tasks or not user_tasks[event.get_user_id()]:
        return
    if event.get_user_id() in user_tasks:
        messages.append({"role": "system", "content": f"用户的提醒任务: {json.dumps(user_tasks[event.get_user_id()])}"})
    messages.append({"role": "user", "content": event.message.extract_plain_text()})
    tool_choice = {"type": "function", "function": {"name": "del_task"}}
    res = await chatbot.chat(messages, event.user_id, str(event.sender.nickname), tool_choice)

    if res.resp_type == "tool_calls":
        msg = await parse_function_call(bot, event, messages, res)
    else:
        msg = res.message["content"]
    await remind_after.send(msg)


# 启动时加载未完成的任务
driver = get_driver()
@driver.on_bot_connect
async def _(bot: Bot):
    await reschedule_tasks(bot)



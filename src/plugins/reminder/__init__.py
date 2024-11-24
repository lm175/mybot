from nonebot.adapters.onebot.v11 import Bot, MessageEvent

from nonebot.rule import to_me
from nonebot import on_regex

from .model import chatbot, Reminder
from .utils import tools, parse_function_call


remind_after = on_regex(
    r'([零一二两三四五六七八九十]+|\d+)个?(秒|分钟|小时|天|星期|周|月|年|世纪)[之以过]?后(提醒|喊|让|叫)我(.*?)$',
    priority=8,
    rule=to_me()
)
remind_time = on_regex(
    r'(今|明)?天?(早|上|下|晚|中)?[午上]?([零一二两三四五六七八九十]+|\d+)(:|：|点钟?整?)零?([零一二三四五六七八九十]+|\d+|半|整|一刻)?分?(提醒|喊|让|叫)我(.*?)$',
    priority=8,
    rule=to_me()
)

@remind_time.handle()
@remind_after.handle()
async def _(bot: Bot, event: MessageEvent):
    messages = [{"role": "user", "content": event.message.extract_plain_text()}]
    tool_choice = {"type": "function", "function": {"name": "set_task"}}
    res = await chatbot.create(
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        user_id=str(event.user_id),
        user_name=str(event.sender.nickname)
    )
    if res.choice.finish_reason == "tool_calls":
        msg = await parse_function_call(bot, event, messages, res)
    else:
        msg = res.message.content
    await bot.send(event, msg)
    




import json

cancel_remind = on_regex(r'((别|不要)(提醒|喊|叫)我?(.*?)了)|(取消|删除)提醒', priority=8, rule=to_me())

@cancel_remind.handle()
async def _(bot: Bot, event: MessageEvent):

    messages: list[dict] = []

    reminder = Reminder(bot)
    user_tasks = reminder.get_user_tasks(event.user_id)
    if user_tasks:
        messages.append({
            "role": "system",
            "content": f"用户的提醒任务: {json.dumps(user_tasks)}"
        })

    messages.append({
        "role": "user",
        "content": event.message.extract_plain_text()
    })
    tool_choice = {"type": "function", "function": {"name": "del_task"}}

    res = await chatbot.create(
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        user_id=str(event.user_id),
        user_name=str(event.sender.nickname)
    )

    if res.choice.finish_reason == "tool_calls":
        msg = await parse_function_call(bot, event, messages, res)
    else:
        msg = res.message.content
    await cancel_remind.send(msg)
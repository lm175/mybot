from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent

import json

from .data import Response, Task
from .model import Reminder, chatbot


async def parse_function_call(
        bot: Bot,
        event: MessageEvent,
        messages: list[dict],
        response: Response
) -> Message:
    
    tool_call = response.message.tool_calls[0]
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    reminder = Reminder(bot)
    
    if name == "set_task":
        group_id = event.group_id if isinstance(event, GroupMessageEvent) else 0
        task_info = Task(
            user_id=event.user_id,
            task_id=f"{event.user_id}_{event.message_id}",
            group_id=group_id,
            run_date=args["target_time"],
            event_description=args["remind_words"]
        )
        result = await reminder.set_task(task_info)
    elif name == "del_task":
        task_id = args["task_id"]
        task_info = reminder.get_task(task_id)
        result = await reminder.del_task(task_info)
    else:
        return Message()
    
    messages.append({
        "role": "tool",
        "content": result,
        "tool_call_id": tool_call.id
    })
    res = await chatbot.create(
        messages=messages,
        user_id=event.get_user_id(),
    )
    return Message(res.message.content)





tools = [
    {
        "type": "function",
        "function": {
            "name": "set_task",
            "description": "为用户设置定时提醒任务，返回一个任务id，用于删除任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_time": {
                        "description": "目标时间，ISO 8601标准, 精确到秒即可",
                        "type": "string"
                    },
                    "remind_words": {
                        "description": "目标时间到达时要对用户说的话",
                        "type": "string"
                    },
                },
                "required": [ "target_time", "remind_words" ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "del_task",
            "description": "为用户删除提醒任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "description": "任务id",
                        "type": "string"
                    },
                "required": [ "task_id" ]
                }
            }
        }
    }
]
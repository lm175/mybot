from nonebot.plugin import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, MessageEvent, GroupMessageEvent
from nonebot.log import logger

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import json

from .config import plugin_config
from .test.model import chatbot, ChatResponse

def load_from_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
def save_to_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


path = plugin_config.tasks_path


async def set_remind(bot: Bot, event: MessageEvent, event_description: str, delay: timedelta):
    """
    设置提醒任务
    """
    user_tasks = load_from_json(path)
    # if delay.total_seconds() > plugin_config.limit:
    #     return "抱歉，这时间太久了，我也记不住呢"

    user_id = event.get_user_id()
    task_id = f"{user_id}_{event.message_id}"
    group_id = 0
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id

    target_datetime = datetime.now() + delay
    scheduler.add_job(
        remind_user,
        "date",
        run_date=target_datetime,
        args=(bot, task_id),
        id=task_id
    )
    
    task_info = {
        "task_id": task_id,
        "group_id": group_id,
        "run_date": target_datetime.isoformat(),  # 转换为目标时间的ISO格式字符串
        "event_description": event_description,
    }

    if user_id not in user_tasks:
        user_tasks[user_id] = []
    user_tasks[user_id].append(task_info)
    save_to_json(path, user_tasks)

    return f"设置成功，任务id: {task_id}"

    delay_seconds = delay.total_seconds()
    delay_days = int(delay_seconds // 86400)
    delay_hours = int(delay_seconds % 86400 // 3600)
    delay_minuts = int(delay_seconds % 86400 % 3600 // 60)
    if delay_days == 0:
        return f"好的，我将在{delay_hours}小时{delay_minuts}分钟后提醒你{event_description}。\n发“/取消{event.message_id}”可取消"
    else:
        return f"好的，我将在{delay_days}天{delay_hours}小时后提醒你{event_description}。\n发“/取消{event.message_id}”可取消"





async def remind_user(bot: Bot, task_id: str):
    """
    发送提醒消息并清理已完成提醒任务
    """
    user_tasks = load_from_json(path)
    user_id = next((uid for uid, tasks in user_tasks.items() if any(t["task_id"] == task_id for t in tasks)), None)
    if user_id is None:
        logger.warning(f"尝试提醒的任务ID {task_id} 不存在于记录中。")
        return

    task_info = next((task for task in user_tasks[user_id] if task["task_id"] == task_id), None)
    event_description = task_info["event_description"]
    group_id = task_info.get("group_id", 0)

    try:
        if group_id:
            await bot.send_group_msg(
                group_id=group_id,
                message=MessageSegment.at(user_id) + f" {event_description}"
            )
        else:
            await bot.send_private_msg(
                user_id=user_id,
                message=event_description
            )

        # 发送成功后，从内存和文件中清理任务
        for user_id, tasks in user_tasks.copy().items():
            user_tasks[user_id] = [task for task in tasks if task["task_id"] != task_id]
            if not user_tasks[user_id]:
                del user_tasks[user_id]

        save_to_json(path, user_tasks)
        
        logger.info(f"任务 {task_id} 已提醒并成功清理。")
    except Exception as e:
        logger.error(f"发送提醒消息或清理任务 {task_id} 失败: {e}")


async def cancel_(task_id: str, user_id: str):
    user_tasks: dict[str, list[dict[str, Any]]] = load_from_json(path)
    # task_id = f"{user_id}_{task_id}"
    user_info = user_tasks[user_id]
    task: dict[str, Any] = {}
    for t in user_info:
        if t["task_id"] == task_id:
            task = t
    if task:
        try:
            scheduler.remove_job(task_id)
            user_info.remove(task)
            user_tasks[user_id] = user_info
            save_to_json(path, user_tasks)

            run_date = datetime.fromisoformat(task["run_date"])
            event_description = task.get("event_description")
            return f"已取消{run_date}{event_description}的提醒"
        except Exception as e:
            return f"取消失败：{e}"
    else:
        return '无效的task_id，请检查参数'




async def reschedule_tasks(bot: Bot):
    user_tasks = load_from_json(path)
    for user_id, tasks in list(user_tasks.items()):  # 使用list以允许在遍历时删除项
        for task_info in list(tasks):
            task_id = task_info["task_id"]
            run_date_str = task_info["run_date"]
            
            run_date = datetime.strptime(run_date_str, "%Y-%m-%dT%H:%M:%S")
            current_time = datetime.now()
            
            if run_date > current_time:
                try:
                    scheduler.add_job(
                        remind_user,
                        "date",
                        run_date=run_date,
                        args=(bot, task_id),
                        id=task_id
                    )
                except Exception as e:
                    logger.info(f"任务添加失败:{e}")
            else:
                tasks.remove(task_info)
                if not tasks:
                    del user_tasks[user_id]
                logger.info(f"任务 {task_id} 因过期已从记录中移除。")
               
    save_to_json(path, user_tasks)



async def parse_function_call(bot: Bot, event: MessageEvent, messages: list[dict], response: ChatResponse) -> Message:
    tool_call = response.message["tool_calls"][0]
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    if name == "set_task":
        target_time = datetime.strptime(args["target_time"], "%Y-%m-%dT%H:%M:%S")
        current_time = datetime.now()
        delay = target_time - current_time
        if delay.total_seconds() < 1:
            delay = timedelta(seconds=3)
        result = await set_remind(bot, event, args["remind_words"], delay)
    elif name == "del_task":
        task_id = args["task_id"]
        print(task_id)
        result = await cancel_(task_id, event.get_user_id())
    else:
        return await parse_function_call(bot, event, messages, response)
    
    messages.append({
        "role": "tool",
        "content": result,
        "tool_call_id":tool_call["id"]
    })
    res = await chatbot.chat(messages, event.user_id, str(event.sender.nickname))
    return Message(res.message["content"])
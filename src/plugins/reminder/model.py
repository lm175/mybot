import time, json
from datetime import datetime, timedelta
from typing import Any
from httpx import AsyncClient
import jwt

from .config import config
from .data import Task, Response

from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.log import logger

from nonebot import require
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")
import nonebot_plugin_localstore as store
from nonebot_plugin_apscheduler import scheduler


class Reminder:

    data_path = store.get_plugin_data_file("tasks.json")
    tasks: list[Task]

    @classmethod
    def load_tasks(cls) -> None:
        try:
            with open(cls.data_path, 'r', encoding='utf-8') as f:
                raw_tasks: list[dict] = json.load(f)
                cls.tasks = [Task(**task_info) for task_info in raw_tasks]
        except Exception as e:
            cls.tasks = []
    
    @classmethod
    def save_tasks(cls) -> None:
        with open(cls.data_path, 'w', encoding='utf-8') as f:
            task_dicts = [task.__dict__ for task in cls.tasks]
            json.dump(task_dicts, f, ensure_ascii=False, indent=4)

    @classmethod
    def get_task(cls, task_id: str) -> Task:
        for t in cls.tasks:
            if t.task_id == task_id:
                return t
        return Task()
    
    @classmethod
    def get_user_tasks(cls, user_id: int) -> list[dict[str, Any]]:
        result = []
        for t in cls.tasks:
            if t.user_id == user_id:
                result.append(t.__dict__)
        return result


    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    async def set_task(self, task_info: Task) -> str:
        current_time = datetime.now()
        run_date = datetime.strptime(task_info.run_date, "%Y-%m-%dT%H:%M:%S")
        if run_date < current_time:
            run_date = current_time + timedelta(seconds=2)
        scheduler.add_job(
            self.remind_user,
            "date",
            run_date=datetime.strptime(task_info.run_date, "%Y-%m-%dT%H:%M:%S"),
            args=(task_info,),
            id=task_info.task_id
        )
        self.__class__.tasks.append(task_info)
        return f"设置成功，任务id: {task_info.task_id}"
    

    async def del_task(self, task_info: Task) -> str:
        flag = False
        for t in self.__class__.tasks:
            if t.task_id == task_info.task_id:
                flag = True
                break
        if flag:
            scheduler.remove_job(task_info.task_id)
            self.__class__.tasks.remove(task_info)
            return f"已取消{task_info.run_date}{task_info.event_description}的提醒"
        else:
            return "无效的task_id，请检查参数"


    async def remind_user(self, task_info: Task) -> None:
        try:
            if task_info.group_id:
                await self.bot.send_group_msg(
                    group_id=task_info.group_id,
                    message=MessageSegment.at(task_info.user_id) + " " + task_info.event_description
                )
            else:
                await self.bot.send_private_msg(
                    user_id=task_info.user_id,
                    message=task_info.event_description
                )
            self.__class__.tasks.remove(task_info)
        except Exception as e:
            logger.error(f"发送提醒消息 {task_info.task_id} 失败: {e}")



    async def reschedule_tasks(self) -> None:
        del_list: list[Task] = []
        current_time = datetime.now()
        for task_info in self.__class__.tasks:
            run_date = datetime.strptime(task_info.run_date, "%Y-%m-%dT%H:%M:%S")
            if run_date < current_time:
                del_list.append(task_info)
            else:
                scheduler.add_job(
                    self.remind_user,
                    "date",
                    run_date=run_date,
                    args=(task_info,),
                    id=task_info.task_id
                )
        for t in del_list:
            self.__class__.tasks.remove(t)



from nonebot import get_driver
driver = get_driver()

@driver.on_startup
async def start():
    Reminder.load_tasks()

@driver.on_bot_connect
async def bot_connect(bot: Bot):
    reminder = Reminder(bot)
    await reminder.reschedule_tasks()

@driver.on_shutdown
async def close():
    Reminder.save_tasks()



class ChatBot:

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._exp = 0
        self._access_token = ""
    
    @property
    def headers(self):
        timestamp = int(round(time.time() * 1000))
        if timestamp >= self._exp:
            self._generate_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }

    def _generate_token(self) -> None:
        try:
            id, secret = self.api_key.split(".")
        except Exception as e:
            raise Exception("invalid apikey", e)

        self._exp = int(round(time.time() * 1000)) + 1800 * 1000
        payload = {
            "api_key": id,
            "exp": self._exp,
            "timestamp": int(round(time.time() * 1000)),
        }
        self._access_token = jwt.encode(
            payload,
            secret,
            algorithm="HS256",
            headers={"alg": "HS256", "sign_type": "SIGN"},
        )


    async def create(
            self,
            model: str = "glm-4-plus",
            messages: list[dict] = [],
            tools: list[dict] = [],
            tool_choice: dict = {},
            user_id: str = "",
            user_name: str = ""
    ) -> Response:
        formatted_now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        setting = (
            f"{config.glm_default_setting}\n"
            f"[现在时间 {formatted_now}]\n"
            f"下面继续你和用户“{user_name}的对话”"
        )
        messages.insert(-2, {"role": "system", "content": setting})
        data = {
            "model": model,
            "messages": messages,
            "user_id": user_id
        }
        if tools:
            data["tools"] = tools
        if tool_choice:
            data["tool_choice"] = tool_choice

        async with AsyncClient() as cli:
            response = await cli.post(
                url=self.url,
                headers=self.headers,
                json=data
            )
        return Response(**response.json())



chatbot = ChatBot(api_key=config.glm_api_key)
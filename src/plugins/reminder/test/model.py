from httpx import AsyncClient
import time, jwt
from datetime import datetime

from .config import config


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
                "required": [ "target_time", "remind_words" ]
                }
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


class ChatResponse:
    def __init__(self, response: dict):
        self.response = response
        self.finish_reason = response["choices"][0]["finish_reason"]
        if self.finish_reason == "stop":
            self.resp_type = "content"
        elif self.finish_reason == "tool_calls":
            self.resp_type = "tool_calls"
        else:
            self.resp_type = ""
        self.request_id = response["request_id"]
        self.model = response["model"]
        self.message = response["choices"][0]["message"]
        self.usage = response["usage"] 




class ChatBot:

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: str, model: str, setting: str):
        self.api_key = api_key
        self.model = model
        self.setting = setting
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

    def _generate_token(self):
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


    async def chat(self, messages: list[dict], user_id: int, username: str = "", tool_choice: dict = {}) -> ChatResponse:
        formatted_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        setting = f"{self.setting}\n[现在时间 {formatted_now}]\n下面继续你和用户“{username}的对话”"
        messages.insert(-2, {"role": "system", "content": setting})
        data = {
            "model": self.model,
            "messages": messages,
            "user_id": str(user_id)
        }
        if tool_choice:
            data["tools"] = tools
            data["tool_choice"] = tool_choice
        print(data)
        async with AsyncClient() as cli:
            response = await cli.post(
                url=self.url,
                headers=self.headers,
                json=data
            )
        print(response.json())
        return ChatResponse(response.json())


chatbot = ChatBot(api_key=config.glm_api_key, model="glm-4-plus", setting=config.glm_default_setting)
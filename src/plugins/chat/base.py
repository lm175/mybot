from nonebot.adapters.onebot.v11 import Message
from abc import ABC, abstractmethod

import asyncio, json, copy
CHATLOCK = asyncio.Lock()

from .config import DATA_PATH


class UserData:
    path = DATA_PATH / "records.json"
    data: dict[str, dict] = {}

    default_data = {
        "current_model": "chatglm",
        "chatglm": {
            "identity": "default",
            "records": {}
        },
        "通义千问": {
            "identity": "default",
            "records": {}
        }
    }


    def __init__(self, user_id: str) -> None:
        user_data = self.__class__.data.get(user_id)
        if not user_data:
            user_data = copy.deepcopy(self.default_data)
        current_model = user_data.get("current_model")
        identity = user_data.get(current_model).get("identity")
        records = user_data.get(current_model).get("records")

        self.user_id = user_id
        self.user_data = user_data
        self.current_model = current_model
        self.identity = identity
        self.records = records


    @classmethod
    def load_users_data(cls) -> None:
        try:
            with open(cls.path, 'r', encoding='utf-8') as f:
                cls.data = json.load(f)
        except:
            cls.data = {}

    @classmethod
    def save_users_data(cls) -> None:
        with open(cls.path, 'w', encoding='utf-8') as f:
            json.dump(cls.data, f, ensure_ascii=False, indent=4)
    
    @classmethod
    def get_all_models(cls) -> list[str]:
        models = [key for key in cls.default_data.keys() if key != "current_model"]
        return models


    def update_user_data(self) -> None:
        self.__class__.data[self.user_id] = self.user_data
        self.save_users_data()

    def update_records(self, records: dict) -> None:
        self.records = records
        self.user_data[self.current_model]["records"] = records
        self.update_user_data()
    
    def change_identity(self, identity: str) -> None:
        self.identity = identity
        self.user_data[self.current_model]["identity"] = identity
        self.update_user_data()
    
    def change_model(self, model: str) -> None:
        self.current_model = model
        self.user_data["current_model"] = model
        self.update_user_data()

UserData.load_users_data()



class ChatBotMessage:

    def __init__(self, text: str, images: list[bytes], user: UserData):
        self.text = text
        self.images = images
        self.user = user


class BaseBot(ABC):

    @abstractmethod
    async def ask(self, message: ChatBotMessage) -> Message:
        ...
    
    @abstractmethod
    async def ask_directly(self, message: ChatBotMessage) -> Message:
        ...
    
    @abstractmethod
    async def clear(self, user_id: str) -> bool:
        ...
    
    @abstractmethod
    async def changeidentity(self, user_id: str, text: str) -> None:
        ...

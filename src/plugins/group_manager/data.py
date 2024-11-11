import json, shutil
from pathlib import Path

from httpx import AsyncClient

from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store


class GroupWelcomData:
    data_dir = store.get_plugin_data_dir()
    data_path = data_dir / "group_welcom.json"
    data: dict[str, str] = {}
    pic_path = data_dir / "pictures" # 图片目录
    

    @classmethod
    def load_welcom_data(cls) -> None:
        try:
            with open(cls.data_path, 'r', encoding='utf-8') as f:
                cls.data = json.load(f)
        except:
            cls.data = {}
        cls.pic_path.mkdir(exist_ok=True)

    @classmethod
    def save_welcom_data(cls) -> None:
        with open(cls.data_path, 'w', encoding='utf-8') as f:
            json.dump(cls.data, f, ensure_ascii=False, indent=4)
    

    def __init__(self, group_id: str) -> None:
        self.group_id = group_id
        if group_id in self.data:
            self.welcom_text = self.data[group_id]
        else:
            self.welcom_text = "欢迎新同学加入本群！"
        self.images_path = self.pic_path / f"{group_id}"
    

    async def get_welcom_msg(self) -> Message:
        message = Message(self.welcom_text)
        if self.images_path.exists():
            for f in self.images_path.iterdir():
                message += MessageSegment.image(f)
        return message

    
    async def set_group_welcom(self, text: str, images: list[str]) -> None:
        if images:
            if Path(self.images_path).exists():
                shutil.rmtree(self.images_path)
            self.images_path.mkdir(parents=True, exist_ok=True) # 清空再创建

            async with AsyncClient() as cli:
                for i, img in enumerate(images):
                    res = await cli.get(img)
                    file_path = self.images_path / f"{i}.png"
                    with open(file_path, 'wb') as f:
                        f.write(res.content)
        self.welcom_text = text
        self.__class__.data[self.group_id] = self.welcom_text



from nonebot import get_driver

driver = get_driver()

@driver.on_startup
async def start():
    GroupWelcomData.load_welcom_data()


@driver.on_shutdown
async def close():
    GroupWelcomData.save_welcom_data()
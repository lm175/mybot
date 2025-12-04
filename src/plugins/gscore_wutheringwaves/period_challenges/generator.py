import json
from pathlib import Path
from typing import Optional

from httpx import AsyncClient, HTTPStatusError

from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import template_to_pic
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

from .error import PeriodNotFoundError


class ImageGenerator:

    base_url: str

    async def fetch_challenge_data(self, period_id: str) -> dict:
        url = f'{self.base_url}/{period_id}.json'
        try:
            async with AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except HTTPStatusError:
            raise PeriodNotFoundError(f"Period ID {period_id} not found.")
    
    async def generate_images(self, period_id: str) -> list[bytes]:
        ...

    # async def fetch_tower_data(self, period_id: str) -> dict:
    #     url = f'https://api.hakush.in/ww/data/zh/tower/{period_id}.json'
    #     async with AsyncClient() as client:
    #         response = await client.get(url)
    #         response.raise_for_status()
    #         return response.json()
    
    # async def fetch_slash_data(self, period_id: str) -> dict:
    #     url = f'https://api.hakush.in/ww/data/zh/slash/{period_id}.json'
    #     async with AsyncClient() as client:
    #         response = await client.get(url)
    #         response.raise_for_status()
    #         return response.json()


class TowerImageGenerator(ImageGenerator):
    base_url = 'https://api.hakush.in/ww/data/zh/tower'

    async def generate_images(self, period_id: str) -> list[bytes]:
        tower_data = await self.fetch_challenge_data(period_id)

        template_path = str(Path(__file__).parent / "templates")
        template_name = "tower.html"
        
        pics = []
        for area_id in tower_data['Area']:
            area_data = tower_data['Area'][area_id]
            area_data['AreaId'] = area_id
            area_data['PeriodId'] = period_id

            pic = await template_to_pic(
                template_path=template_path,
                template_name=template_name,
                templates= {'area_data': area_data},
                pages={
                    "viewport": {"width": 600, "height": 300},
                    "base_url": f"file://{template_path}",
                },
                wait=5,
            )
            pics.append(pic)

        return pics


class SlashImageGenerator(ImageGenerator):
    base_url = 'https://api.hakush.in/ww/data/zh/slash'

    async def generate_images(self, period_id: str) -> list[bytes]:
        slash_data = await self.fetch_challenge_data(period_id)

        template_path = str(Path(__file__).parent / "templates")
        template_name = "slash.html"

        pics = []

        # 按照ID排序关卡数据
        sorted_keys = sorted(slash_data['Id'].keys(), key=lambda k: int(k))
        sorted_values = [slash_data['Id'][k] for k in sorted_keys]
        
        # 获取最后一关数据
        last_stage_data = sorted_values[-1]
        last_stage_data["PeriodId"] = period_id
        pic = await template_to_pic(
            template_path=template_path,
            template_name=template_name,
            templates={"data": last_stage_data},
            pages={
                "viewport": {"width": 800, "height": 600},
                "base_url": f"file://{template_path}",
            },
            wait=2,
        )
        pics.append(pic)

        
        # 获取第二关信物数据
        second_stage_data = sorted_values[1]
        slash_tokens: list[dict[str, int]] = second_stage_data.get("LevelPassReward", [])
        for token in slash_tokens:
            item_id = str(token.get("Key"))
            item_data = await self.fetch_item_data_from_local()
            if item_id in item_data:
                pic = await template_to_pic(
                    template_path=template_path,
                    template_name="item.html",
                    templates={"relic": item_data[item_id]},
                    pages={
                        "viewport": {"width": 400, "height": 400},
                        "base_url": f"file://{template_path}",
                    },
                    wait=5,
                )
                pics.append(pic)

        return pics

    async def fetch_item_data_from_local(self) -> dict:
        try:
            stroed_items = store.get_plugin_data_file("item_all.json")
            with open(stroed_items, 'r', encoding='utf-8') as f:
                res = json.load(f)
            return res
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        return await self.fetch_item_data_from_api()

    async def fetch_item_data_from_api(self) -> dict:
        url = "https://api.hakush.in/ww/data/zh/item_all.json"
        async with AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            res = response.json()
        stored_items = store.get_plugin_data_file("item_all.json")
        with open(stored_items, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        return res
    


class ImageHandler:
    async def get_images_from_local(self, img_type: str, period_id: str) -> Optional[list[bytes]]:
        data_dir = store.get_plugin_data_dir()
        challenge_dir = data_dir / img_type / period_id
        pics: list[bytes] = []
        if challenge_dir.exists() and any(challenge_dir.iterdir()):
            for img_file in sorted(challenge_dir.iterdir()):
                with open(img_file, 'rb') as f:
                    pics.append(f.read())
            return pics
        return None
    
    async def save_images_to_local(self, img_type: str, period_id: str, pics: list[bytes]) -> None:
        data_dir = store.get_plugin_data_dir()
        challenge_dir = data_dir / img_type / period_id
        challenge_dir.mkdir(parents=True, exist_ok=True)
        for idx, pic in enumerate(pics):
            with open(challenge_dir / f"{idx+1}.png", 'wb') as f:
                f.write(pic)


    async def get_images(self, img_type: str, period_id: str) -> list[bytes]:
        if img_type == 'tower':
            generator = TowerImageGenerator()
        elif img_type == 'slash':
            generator = SlashImageGenerator()
        else:
            raise ValueError("Invalid image type. Use 'tower' or 'slash'.")

        pics: list[bytes] = []
        if local_pics := await self.get_images_from_local(img_type, period_id):
            pics = local_pics
        else:
            pics = await generator.generate_images(period_id)
            await self.save_images_to_local(img_type, period_id, pics)

        return pics


async def get_images(img_type: str, period_id: str) -> list[bytes]:
    if img_type == 'tower':
        generator = TowerImageGenerator()
    elif img_type == 'slash':
        generator = SlashImageGenerator()
    else:
        raise ValueError("Invalid image type. Use 'tower' or 'slash'.")

    pics: list[bytes] = []

    # 尝试从本地获取图片
    data_dir = store.get_plugin_data_dir()
    challenge_dir = data_dir / img_type / period_id
    if challenge_dir.exists() and any(challenge_dir.iterdir()):
        for img_file in sorted(challenge_dir.iterdir()):
            with open(img_file, 'rb') as f:
                pics.append(f.read())
    else:
        # 本地无图片，生成新图片
        pics = await generator.generate_images(period_id)
        # 保存图片到本地
        challenge_dir.mkdir(parents=True, exist_ok=True)
        for idx, pic in enumerate(pics):
            with open(challenge_dir / f"{idx+1}.png", 'wb') as f:
                f.write(pic)
    return pics

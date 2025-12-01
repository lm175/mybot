import json
from pathlib import Path
from datetime import datetime
from typing import Callable, TypeVar, Optional, Awaitable
from dataclasses import dataclass

from httpx import AsyncClient

from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import template_to_pic
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store


@dataclass
class PeriodInfo:
    id: str
    begin: datetime
    end: datetime


T = TypeVar('T')

class DataFetcher:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def fetch_from_api(self, endpoint: str) -> dict:
        url = f'{self.base_url}/{endpoint}'
        async with AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            res = response.json()
        file_name = endpoint if endpoint.endswith('.json') else f"{endpoint}.json"
        stored_periods = store.get_plugin_data_file(file_name)
        with open(stored_periods, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        return res

    async def fetch_from_local(self, endpoint: str) -> Optional[dict]:
        try:
            file_name = endpoint if endpoint.endswith('.json') else f"{endpoint}.json"
            stroed_items = store.get_plugin_data_file(file_name)
            with open(stroed_items, 'r', encoding='utf-8') as f:
                res = json.load(f)
            return res
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None
    

class PeriodManager:
    def __init__(self, fetcher: DataFetcher, endpoint: str):
        self.fetcher = fetcher
        self.endpoint = endpoint

    # async def get_periods(self) -> dict[str, PeriodInfo]:
    #     data = await self.fetcher.fetch_from_local(self.endpoint)
    #     if data is None:
    #         data = await self.fetcher.fetch_from_api(self.endpoint)
        
    #     periods = {}
    #     for period_id, info in data.items():
    #         periods[period_id] = PeriodInfo(
    #             id=period_id,
    #             begin=datetime.fromisoformat(info['Begin']),
    #             end=datetime.fromisoformat(info['End'])
    #         )
    #     return periods
    
    async def get_period_data(self, period_id: str) -> PeriodInfo:
        periods = await self.fetcher.fetch_from_local(self.endpoint)
        # {'1': {'begin': '2024-05-27', 'end': '2024-06-10'}, ...}
        if periods is None or period_id not in periods:
            periods = await self.fetcher.fetch_from_api(self.endpoint)
        
        begin_dt = periods[period_id]['begin']
        end_dt = periods[period_id]['end']

        return PeriodInfo(
            id=period_id,
            begin=datetime.fromisoformat(begin_dt),
            end=datetime.fromisoformat(end_dt)
        )
    

    async def get_period_id(self, target_date: str = '') -> str:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        
        # 尝试从本地获取数据
        try:
            periods = await self.fetcher.fetch_from_local(self.endpoint)
            if periods is None:
                raise FileNotFoundError("Local period data not found.")
            result = await self._find_period_id(periods, target_dt)
            return result
        except (FileNotFoundError, ValueError) as e:
            # 如果本地文件不存在或找不到对应周期，从网络获取最新数据
            logger.warning(f"Local period data not found or invalid: {e}. Fetching from API.")
            periods = await self.fetcher.fetch_from_api(self.endpoint)
            result = await self._find_period_id(periods, target_dt)
            return result


    async def _find_period_id(self, periods: dict[str, dict[str, str]], target_dt: datetime) -> str:
        """从给定的周期数据中查找目标日期对应的周期ID"""
        period_list: list[tuple[str, datetime, datetime]] = []
        for k, v in periods.items():
            begin_dt = datetime.strptime(v['begin'], "%Y-%m-%d")
            end_dt = datetime.strptime(v['end'], "%Y-%m-%d")
            period_list.append((k, begin_dt, end_dt))
        
        period_list.sort(key=lambda x: x[1])

        for i, (period_id, begin_dt, end_dt) in enumerate(period_list):
            if begin_dt <= target_dt < end_dt:
                return period_id
            elif target_dt == end_dt: # 日期处于边界时，视为下一期
                if i + 1 < len(period_list):
                    return period_list[i + 1][0]
        
        raise ValueError("No tower period found for the given date.")
    


class ImageGenerator:

    base_url: str

    async def fetch_challenge_data(self, period_id: str) -> dict:
        url = f'{self.base_url}/{period_id}.json'
        async with AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
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
    
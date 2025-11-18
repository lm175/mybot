from httpx import AsyncClient

from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import template_to_pic
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store


from pathlib import Path
from datetime import datetime
import json


async def fetch_tower_data(period_id: str) -> dict:
    url = f'https://api.hakush.in/ww/data/zh/tower/{period_id}.json'
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    

async def generate_tower_images(period_id: str) -> list[bytes]:
    tower_data = await fetch_tower_data(period_id)

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
            wait=2,
        )
        pics.append(pic)

    return pics


async def fetch_periods_from_api() -> dict[str, dict[str, str]]:
    url = 'https://api.hakush.in/ww/data/tower.json'
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        res = response.json()
    stored_periods = store.get_plugin_data_file("tower_periods.json")
    with open(stored_periods, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    return res

async def fetch_periods_from_local() -> dict[str, dict[str, str]]:
    stored_periods = store.get_plugin_data_file("tower_periods.json")
    with open(stored_periods, 'r', encoding='utf-8') as f:
        res = json.load(f)
    return res


async def get_period_id(target_date: str = '') -> str:
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")
    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")
    
    # 尝试从本地获取数据
    try:
        periods = await fetch_periods_from_local()
        result = await _find_period_id(periods, target_dt)
        return result
    except (FileNotFoundError, ValueError) as e:
        # 如果本地文件不存在或找不到对应周期，从网络获取最新数据
        logger.warning(f"Local period data not found or invalid: {e}. Fetching from API.")
        periods = await fetch_periods_from_api()
        result = await _find_period_id(periods, target_dt)
        return result

async def _find_period_id(periods: dict[str, dict[str, str]], target_dt: datetime) -> str:
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



class TowerPeriodData:
    def __init__(self, period_id: str, begin_dt: str, end_dt: str):
        self.period_id = period_id
        self.begin_dt = begin_dt
        self.end_dt = end_dt


async def get_period_data(period_id: str) -> TowerPeriodData:

    periods = await fetch_periods_from_local()
    # {'1': {'begin': '2024-05-27', 'end': '2024-06-10'}, ...}
    if period_id not in periods:
        periods = await fetch_periods_from_api()
    if period_id not in periods:
        raise ValueError("Invalid period ID.")

    begin_dt = periods[period_id]['begin']
    end_dt = periods[period_id]['end']

    return TowerPeriodData(period_id, begin_dt, end_dt)


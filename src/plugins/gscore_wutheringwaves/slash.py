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


async def fetch_slash_data(period_id: str) -> dict:
    url = f'https://api.hakush.in/ww/data/zh/slash/{period_id}.json'
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
        """
        {
            "Id": {
                "73": { ... }, "74": { ... }, ... 
            },
            "Begin": "2025-12-22",
            "End": "2026-01-19",
        }
        """

async def fetch_item_data_from_local() -> dict:
    try:
        stroed_items = store.get_plugin_data_file("item_all.json")
        with open(stroed_items, 'r', encoding='utf-8') as f:
            res = json.load(f)
        return res
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return await fetch_item_data_from_api()

async def fetch_item_data_from_api() -> dict:
    url = "https://api.hakush.in/ww/data/zh/item_all.json"
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        res = response.json()
    stored_items = store.get_plugin_data_file("item_all.json")
    with open(stored_items, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    return res



async def generate_slash_images(period_id: str) -> list[bytes]:
    slash_data = await fetch_slash_data(period_id)

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
        item_data = await fetch_item_data_from_local()
        if item_id in item_data:
            pic = await template_to_pic(
                template_path=template_path,
                template_name="item.html",
                templates={"relic": item_data[item_id]},
                pages={
                    "viewport": {"width": 400, "height": 400},
                    "base_url": f"file://{template_path}",
                },
                wait=2,
            )
            pics.append(pic)

    return pics


async def fetch_periods_from_api() -> dict[str, dict[str, str]]:
    url = 'https://api.hakush.in/ww/data/slash.json'
    async with AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        res = response.json()
    stored_periods = store.get_plugin_data_file("slash_periods.json")
    with open(stored_periods, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    return res

async def fetch_periods_from_local() -> dict[str, dict[str, str]]:
    stored_periods = store.get_plugin_data_file("slash_periods.json")
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
    
    raise ValueError("No slash period found for the given date.")


import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from httpx import AsyncClient

from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

from .error import PeriodNotFoundError


@dataclass
class PeriodInfo:
    id: str
    begin: datetime
    end: datetime


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
        
        try:
            begin_dt = periods[period_id]['begin']
            end_dt = periods[period_id]['end']
        except KeyError:
            raise PeriodNotFoundError(f"Period ID {period_id} not found.")

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

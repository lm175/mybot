import json, datetime, asyncio
from dataclasses import dataclass

from httpx import AsyncClient

from .ninja_redeem import redeem_code as ninja3_redeem_code

@dataclass
class RedeemCodeResponse:
    requestId: str
    code: int
    msg: str
    data: dict

    def __post_init__(self):
        if self.code == 0:
            self.msg = '领取成功，请登录游戏领取奖励邮件'


def is_this_week(date: datetime.date) -> bool:
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)

    return start_of_week <= date <= end_of_week


async def redeem_code(uid: int, code: str) -> RedeemCodeResponse:
    res =  await asyncio.to_thread(ninja3_redeem_code, uid, code)
    while res.json()['code'] == 2156 or res.json()['msg'] == 'Internal Server Error':
        await asyncio.sleep(5)
        res =  await asyncio.to_thread(ninja3_redeem_code, uid, code)
    return RedeemCodeResponse(**res.json())


async def code_checker(code: str) -> bool:
    my_uids = [634431781, 100400416931, 200701467414]
    for uid in my_uids:
        res = await redeem_code(uid, code)
        if res.code == 0 or res.code == 2152:
            return True

    return False


async def query_uid(uid: int) -> str | None:
    async with AsyncClient() as client:
        res = await client.get(f"https://statistics.pandadastudio.com/player/simpleInfo?uid={uid}")
    data: dict[str, str] = res.json().get('data')
    if not data:
        return None
    
    if not data["title"]:
        data["title"] = "禁忍"
    return f"uid: {data['uid']}\n{data['name']} - {int(data['serverId']) + 1}服 - {data['title']}"


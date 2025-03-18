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


def get_server_id(game_id: int) -> int:
    id_str = str(game_id)
    if len(id_str) == 9:
        id_str = '000' + id_str
    return int(id_str[0])


async def redeem_code(uid: int, code: str) -> RedeemCodeResponse:
    res =  await asyncio.to_thread(ninja3_redeem_code, uid, code)
    while res.json()['code'] == 2156 or res.json()['msg'] == 'Internal Server Error':
        await asyncio.sleep(5)
        res =  await asyncio.to_thread(ninja3_redeem_code, uid, code)
    return RedeemCodeResponse(**res.json())


async def code_checker(code: str) -> tuple[list[int], bool]:
    my_uids = [634431781, 100400416931, 200701467414]
    available_servers: list[int] = []
    for i in range(len(my_uids)):
        resp = await redeem_code(my_uids[i], code)
        if resp.code == 0 or resp.code == 2152:
            available_servers.append(i)
    is_universal = len(available_servers) == len(my_uids)
    return available_servers, is_universal


async def query_uid(uid: int) -> str | None:
    async with AsyncClient() as client:
        res = await client.get(f"https://statistics.pandadastudio.com/player/simpleInfo?uid={uid}")
    data: dict[str, str] = res.json().get('data')
    if not data:
        return None
    
    if not data["title"]:
        data["title"] = "禁忍"
    return f"uid: {data['uid']}\n{data['name']} - {int(data['serverId']) + 1}服 - {data['title']}"


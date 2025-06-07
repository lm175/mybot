from nonebot import on_command
from nonebot.params import CommandArg, ArgPlainText
from nonebot.typing import T_State
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11.helpers import is_cancellation, extract_numbers

from httpx import AsyncClient
import asyncio

from .draw import creat_table, draw_search_res


from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="QQ音乐点歌",
    description="QQ音乐点歌",
    usage=(
        "/QQ点歌 <歌曲名>\n"
        "    介绍：搜索歌曲\n"
        "/QQ语音\n"
        "    介绍：把刚点的歌以语音形式发送\n"
        "/QQ直链\n"
        "    介绍：发送刚点的歌的下载链接\n"
    )
)


async def get_song_list(name) -> list[dict[str, str]]:
    url = "https://api.dragonlongzhu.cn/api/dg_QQmusicflac.php"
    params = {
        "msg": name,
        "type": "json"
    }
    try:
        async with AsyncClient() as client:
            res = await client.get(url=url, params=params)
        return res.json()["data"]
    except Exception as e:
        logger.error(e)
        return []

async def get_song(name, n=None) -> dict:
    url = "https://api.dragonlongzhu.cn/api/dg_QQmusicflac.php"
    params = {
        "msg": name,
        "n": n,
        "type": "json"
    }
    try:
        async with AsyncClient() as client:
            res = await client.get(url=url, params=params)
        return res.json()["data"]
    except Exception as e:
        logger.error(e)
        return {}


cache_dict = {}


qqMusic = on_command("QQ点歌", aliases={"qq点歌"}, priority=20, block=True)


@qqMusic.handle()
async def receive_song_name(state: T_State, name: Message = CommandArg()):
    state['cnt'] = 0
    if name.extract_plain_text():
        state["name"] = name


@qqMusic.got("name", prompt="请发送搜索内容，发送 0 退出")
async def got_song_name(name: str = ArgPlainText("name")):
    if not name or name == "0" or is_cancellation(name):
        await qqMusic.finish("已退出搜索")
    song_list = await get_song_list(name)
    res = await creat_table(song_list)
    try:
        pic = await draw_search_res(res)
    except Exception as e:
        logger.error(e)
        await qqMusic.finish(f"绘制歌曲列表失败，请检查后台输出")
    await qqMusic.send(MessageSegment.image(pic))


@qqMusic.receive()
async def send_music(event: MessageEvent, state: T_State, name: str = ArgPlainText("name")):
    msg = event.get_message()
    msg_text = msg.extract_plain_text()
    n = extract_numbers(msg)
    if not msg_text or msg_text == '0' or is_cancellation(msg_text):
        await qqMusic.finish("已退出选择")
    if state["cnt"] >= 3:
        await qqMusic.finish("错误指令过多，已退出选择")

    n = extract_numbers(msg)
    if not n:
        state["cnt"] += 1
        await qqMusic.reject("非正确指令，请重新输入")
    n = int(n[0])

    data = await get_song(name, n)
    await qqMusic.send(MessageSegment.music_custom(
        url=data['link'],
        audio=data['music_url'],
        title=data['song_name'],
        content=data["song_singer"],
        img_url=data['cover']
    ))
    user_id = str(event.user_id)
    cache_dict[user_id] = data
    asyncio.create_task(clean_song_cache(user_id))



qqRecord = on_command("QQ语音", aliases={"qq语音"}, priority=20, block=True)
qqLink = on_command("QQ直链", aliases={"qq直链"}, priority=20, block=True)
# qqLyric = on_command("QQ歌词", aliases={"qq歌词"}, priority=20, block=True)


@qqRecord.handle()
@qqLink.handle()
# @qqLyric.handle()
async def handle_cache(event: MessageEvent):
    user_id = str(event.user_id)
    if user_id not in cache_dict:
        return
    
    song_data = cache_dict[user_id]
    msg = (event.get_message()).extract_plain_text()
    if "语音" in msg:
        await qqRecord.send(MessageSegment.record(song_data['music_url']))
    elif "直链" in msg:
        await qqLink.send(song_data['music_url'])
    else:
        pass



async def clean_song_cache(user_id: str):
    await asyncio.sleep(600)
    del cache_dict[user_id]
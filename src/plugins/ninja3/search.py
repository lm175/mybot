from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.helpers import extract_image_urls
from httpx import AsyncClient

from .requires import store
ZY_PATH = store.get_plugin_data_file("zy.jpg")


zyroad_regex = on_regex(
    r"((终焉|四象|风.?雷|水.?火)(路线|顺序|终焉|四象)?(((怎么|咋)走|(是?(什么|啥))|.*(知道|有[吗嘛]))|啥(boss|BOSS))|((求|知道|有(没有|无)?).*?((终焉|四象|风.?雷|水.?火)(路线|顺序)[吗嘛]?)))",
    priority=11,
    block=True
)

@zyroad_regex.handle()
async def _():
    await zyroad_regex.send(MessageSegment.image(ZY_PATH))



zyroad_update = on_command('更新终焉信息', aliases={'更新终焉路线'}, priority=5, block=True)

@zyroad_update.handle()
async def _(state: T_State, message: Message = CommandArg()):
    if message:
        state["message"] = message

@zyroad_update.got('message', prompt='请发送终焉路线图')
async def _(state: T_State):
    message: Message = state["message"]
    images = extract_image_urls(message)
    if not images:
        await zyroad_update.finish('已取消')
    try:
        async with AsyncClient() as client:
            response = await client.get(url=images[0])
        with open(ZY_PATH, "wb") as f:
            f.write(response.content)
    except:
        await zyroad_update.finish("图片下载失败，请稍后重试")
    
    await zyroad_update.finish("更新成功" + MessageSegment.image(ZY_PATH))
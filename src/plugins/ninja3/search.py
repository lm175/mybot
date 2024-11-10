from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.helpers import extract_image_urls
import json
from httpx import AsyncClient
from .utils import DATA_PATH

from nonebot.plugin import require
require("nonebot_plugin_saa")
from nonebot_plugin_saa import MessageFactory, Text, Image


weapondata = on_command('武器数据', priority=10, block=True)
zyroad_regex = on_regex(
    r"((终焉|四象|风.?雷|水.?火)(路线|顺序|终焉|四象)?(((怎么|咋)走|(是?(什么|啥))|.*(知道|有[吗嘛]))|啥(boss|BOSS))|((求|知道|有(没有|无)?).*?((终焉|四象|风.?雷|水.?火)(路线|顺序)[吗嘛]?)))",
    priority=11,
    block=True
)
zyroad_update = on_command(
    '更新终焉信息',
    aliases={'更新终焉路线'},
    priority=5,
    block=True
)


@weapondata.handle()
async def handle_weapon(arg: Message = CommandArg()):
    weapon_name = arg.extract_plain_text().strip()
    if weapon_name:
        message = await get_weapon_data(weapon_name)
        await weapondata.finish(message)
    else:
        await weapondata.finish(MessageSegment.image(DATA_PATH /'weapon.jpg'))


async def get_weapon_data(weapon_name: str) ->str:
    """
    返回武器的文字数据
    """
    with open(DATA_PATH /'weapon_data.json', 'r', encoding='utf-8') as data_file:
        weapon_data = json.load(data_file)
    if weapon_name in weapon_data:
        return weapon_data[weapon_name]
    
    with open(DATA_PATH /'weapon_name.json', 'r', encoding='utf-8') as name_file:
        name_aliases = json.load(name_file)
    correct_name = next((name for alias, name in name_aliases.items() if alias == weapon_name), None)
    if correct_name:
        return weapon_data[correct_name]

    return '暂未收录该武器'


@zyroad_regex.handle()
async def handle_zy():
    reply = MessageFactory(Image(DATA_PATH /'zy.jpg'))
    with open(DATA_PATH /'zy.txt', 'r', encoding='utf-8') as file:
        text = file.read()
    reply.append(Text(text))
    await reply.finish(reply=True)



@zyroad_update.handle()
async def _handle(state: T_State, message: Message = CommandArg()):
    if message:
        state["message"] = message

@zyroad_update.got('message', prompt='请发送终焉路线图(可附加文字说明)\n发送“取消”可取消')
async def _(state: T_State):
    message = state["message"]
    text = message.extract_plain_text()
    image = extract_image_urls(message)
    if text == '取消':
        await zyroad_update.finish('已取消')

    try:
        async with AsyncClient() as client:
            response = await client.get(url=image[0])
        with open(DATA_PATH /'zy.jpg', "wb") as f:
            f.write(response.content)
    except:
        await zyroad_update.finish("图片下载失败，请稍后重试")

    with open(DATA_PATH /'zy.txt', 'w', encoding='utf-8') as file:
        file.write(text)
    
    await zyroad_update.finish("更新成功" + MessageSegment.image(DATA_PATH /'zy.jpg') + text)




jzzr = on_command('家族招人', priority=5, block=True)

@jzzr.handle()
async def handle_receive():
    await jzzr.finish(MessageSegment.image(DATA_PATH /'jzzr.jpg'))
from .sundry import *
from .star_son import *
from .daily import *

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="乱七八糟的功能",
    description="一些乱七八糟的功能",
    usage=(
        "今日运势 -- 随机运势图\n"
        "今日老婆 -- 随机二次元图\n"
        "疯狂星期四 -- 随机疯四文案\n"
        "/发病 <发病对象> -- 随机逆天文案\n"
        " \n"
        "赞我 -- 给你资料卡点10个赞\n"
        "/raw -- 查看消息源码\n"
        " \n"
        "戳一戳有概率反击"
    )
)

from .search import *
from .dhm import *
from .uid_bind import *
from .remind import *

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="忍3",
    description="忍者必须死3相关功能",
    usage=(
        "忍3绑定uid <你的uid>\n"
        "    介绍：自动兑换每周兑换码，加好友会收到提醒\n"
        "    示例：忍3绑定uid 634431781\n"
        "忍3解除绑定 <你的uid>\n"
        "    介绍：解除已绑定的uid，一个qq最多绑定5个\n"
        "    示例：忍3解除绑定 634431781\n"
        "uid查询 <要查的uid>\n"
        "    介绍：查询账号的基本信息\n"
        "    示例：uid查询 634431781\n"
        "终焉咋走\n"
        "    介绍：查看本周终焉路线图\n"
        " \n"
        "Tip：\n"
        "兑换码和终焉图是手动更新，如果您感觉管理员太慢可以帮它\n"
        "更新兑换码 <兑换码内容>\n"
        "更新终焉路线 <终焉路线图>\n（路线图暂时没有检测机制，请不要乱传图片）"
    )
)
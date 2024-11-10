from nonebot.plugin import PluginMetadata
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="聊天截图伪造",
    description="伪造QQ聊天截图，参考消息伪造插件",
    usage="qq说...+qq说...",
    extra={
        "example": "1756000830说111+2328614294说你好 有什么能帮你的吗？"
    },
    type="application",
    homepage="https://github.com/lm175/nonebot-plugin-fakepic.git",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

from . import __main__ 
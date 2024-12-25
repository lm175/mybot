from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="聊天截图伪造",
    description="伪造QQ聊天截图",
    usage=(
        "qq号说+...qq号说...\n"
        "   “+” 分隔不同用户\n"
        "   “ ” 分隔同一用户的每条消息\n"
        "示例：\n"
        "1756000830说哈喽+2328614294说你好 有什么能帮你的吗？"
    )
)

from . import __main__ 
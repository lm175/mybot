from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="转人工",
    description="联系管理员",
    usage=(
        "发送“/转人工 消息内容”可将消息转发至管理员\n"
    ),
)

from .handler import hunman_switch, admin_reply

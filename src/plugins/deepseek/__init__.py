from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="AI对话",
    description="AI聊天插件",
    usage=(
        "@机器人 <你要说的内容>\n"
        "   介绍：触发AI对话\n"
        "   示例：@机器人 早上好\n"
        " \n"
        "/clear\n"
        "   介绍：清除记忆（仅私聊）"
    ),
    extra={
        "notice": "每个群聊和私聊都是独立会话",
    },
)

from . import main, commands
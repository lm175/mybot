from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="WutheringWaves",
    description="全功能鸣潮查询插件",
    usage=(
        "发送“ww帮助”查看功能列表"
    ),
)

from nonebot import on_fullmatch

wwhelp = on_fullmatch("ww帮助", priority=1, block=True)
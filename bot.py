import nonebot
from nonebot.adapters.onebot.v11 import Adapter as Onebot_V11_Adapter

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(Onebot_V11_Adapter)

# 在这里加载插件
nonebot.load_builtin_plugins("echo")  # 内置插件
nonebot.load_from_toml("pyproject.toml", encoding="utf-8")

if __name__ == "__main__":
    nonebot.run()

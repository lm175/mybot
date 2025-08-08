from nonebot import on_command
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11.helpers import extract_numbers
from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import template_to_pic

from datetime import datetime
from dataclasses import dataclass

from pathlib import Path
path = Path(__file__).parent

from .utils import get_date, caculator


@dataclass
class CurrentResources:
    common: int
    rare: int
    epic: int
    legendary: int
    common_shard: int
    rare_shard: int
    epic_shard: int
    legendary_shard: int
    random_shard: int

@dataclass
class ExpectedResources:
    universal_shard: int
    attribute_shard: int
    random_attribute_shard: int
    common_shard: int
    rare_shard: int
    epic_shard: int
    legendary_shard: int
    random_shard: int


async def render(templates: dict) -> bytes:
    template_path = str(Path(__file__).parent / "templates")

    return await template_to_pic(
        template_path=template_path,
        template_name="activity_report.html",
        templates=templates,
        pages={
            "viewport": {"width": 1000, "height": 300},
            "base_url": f"file://{template_path}",
        },
    )


cbt = on_command("藏宝图", aliases={"cbt"}, priority=10, block=True)

@cbt.handle()
async def handle_caculate(event: MessageEvent):
    """
    输入顺序应为：凡品，珍品，绝品，神品，凡品碎片，珍品碎片，绝品碎片，神品碎片，随机碎片
    取前9个参数进行计算，若参数不足9则将后面的参数设置为0
    """

    receive_list = extract_numbers(event.get_message())
    current_list = [0] * 9
    for i in range(len(receive_list)):
        if i >= 9:
            break
        current_list[i] = int(receive_list[i])

    # 计算
    end_date = datetime(2025, 9, 4, 5)
    days, weeks = await get_date(end_date)
    current_resources = CurrentResources(*current_list)
    expected_resources = ExpectedResources(*(await caculator(current_list, days, weeks)))

    templates = {
        "days": days,
        "weeks": weeks,
        "end_date": end_date.strftime("%Y-%m-%d"),
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "current_resources": current_resources.__dict__,
        "expected_resources": expected_resources.__dict__,
    }

    await cbt.finish(MessageSegment.image(await render(templates)))


__all__ = [
    "cbt"
]
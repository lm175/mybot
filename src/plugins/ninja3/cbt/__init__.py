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

from .utils import get_date, caculator, get_total_element_fragment


@dataclass
class CurrentResources:
    common: int
    rare: int
    epic: int
    legendary: int
    common_fragment: int
    rare_fragment: int
    epic_fragment: int
    legendary_fragment: int
    random_fragment: int
    wind: int
    thunder: int
    water: int
    fire: int
    universal_fragment: int

@dataclass
class ExpectedResources:
    universal_fragment: int
    element_fragment: int
    random_element_fragment: int
    common_fragment: int
    rare_fragment: int
    epic_fragment: int
    legendary_fragment: int
    random_fragment: int

@dataclass
class Total:
    universal_fragment: int
    element_fragment: int
    random_element_fragment: int
    element_icon: str
    element_name: str



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
    if event.get_message().extract_plain_text().strip() == "藏宝图指令模板":
        message = MessageSegment.node_custom(
            user_id=event.self_id,
            nickname="",
            content=(
                "/cbt\n"
                "凡品 0\n"
                "珍品 0\n"
                "绝品 0\n"
                "神品 0\n"
                "凡品碎片 0\n"
                "珍品碎片 0\n"
                "绝品碎片 0\n"
                "神品碎片 0\n"
                "随机碎片 0\n"
                "风残卷 0\n"
                "雷残卷 0\n"
                "水残卷 0\n"
                "火残卷 0\n"
                "通用残卷 0"
            )
        ) + MessageSegment.node_custom(
            user_id=event.self_id,
            nickname="",
            content="请将以上指令复制到聊天框中，修改数字后发送即可"
        ) + MessageSegment.node_custom(
            user_id=event.self_id,
            nickname="",
            content="如果您记得顺序，也可以省略文字，如：\n/cbt 1 2 3 4 5 6 7 8 9 100 200 300 400 500\n"
        ) + MessageSegment.node_custom(
            user_id=event.self_id,
            nickname="",
            content="更详细的分析可参考：https://bspombul.html2web.com/"
        )
        await cbt.finish(message)

    receive_list = extract_numbers(event.get_message())
    current_list = [0] * 14
    for i in range(len(receive_list)):
        if i >= len(current_list):
            break
        current_list[i] = int(receive_list[i])

    # 计算
    end_date = datetime(2026, 3, 5, 5)
    days, weeks = await get_date(end_date)
    current_resources = CurrentResources(*current_list)
    expected_resources = ExpectedResources(*(await caculator(current_list, days, weeks)))
    max_element, max_element_value, converted_element_fragment = await get_total_element_fragment(current_list)
    element_icon = {"风": "wind", "雷": "thunder", "水": "water", "火": "fire"}
    total = Total(
        universal_fragment=current_list[13] + expected_resources.universal_fragment + converted_element_fragment, # 通用残卷
        element_fragment=expected_resources.element_fragment + max_element_value, # 属性残卷
        random_element_fragment=expected_resources.random_element_fragment, # 随机属性残卷
        element_icon=element_icon.get(max_element, "wind"),
        element_name=max_element
    )
    # 计算仅保留通用残卷的数量
    total_universal_fragment = total.universal_fragment
    total_universal_fragment += total.element_fragment // 2 + total.random_element_fragment // 2

    templates = {
        "days": days,
        "weeks": weeks,
        "end_date": end_date.strftime("%Y-%m-%d"),
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "current_resources": current_resources.__dict__,
        "expected_resources": expected_resources.__dict__,
        "total": total.__dict__,
        "total_universal_fragment": total_universal_fragment,
    }

    await cbt.send(MessageSegment.image(await render(templates)))
    if not receive_list:
        await cbt.send("提示：未输入参数，发送“藏宝图指令模板”可获取格式参考")


__all__ = [
    "cbt"
]
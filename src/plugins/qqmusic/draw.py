from pil_utils import BuildImage, Text2Image
from pil_utils.types import HAlignType
from dataclasses import dataclass
from typing import List, Dict, NamedTuple, Optional

from .nonebot_plugin_multincm.draw.pil import draw_table, BACKGROUND, TableHead
from .nonebot_plugin_multincm.config import config


class Table(NamedTuple):
    head: List[TableHead]
    rows: List[List[str]]


async def creat_table(song_list: List[Dict[str, str]]) -> Table:
    """
    将api返回的列表转换成表格对象
    """
    head = [
        TableHead(name="序号"),
        TableHead(name="歌名"),
        TableHead(name="歌手")
    ]
    rows = []
    song_list = [{k: str(v) for k, v in d.items()} for d in song_list]
    for song in song_list:
        rows_list = list(song.values())
        rows.append(rows_list)
    return Table(head=head, rows=rows)



async def draw_search_res(res: Table) -> bytes:
    pic_padding = 50
    table_padding = 20
    table_border_radius = 15

    heads, lines = res
    table_img = draw_table(heads, lines, border_radius=table_border_radius)

    title_txt = Text2Image.from_text(
        "歌曲列表",
        80,
        weight="bold",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )
    tip_txt = Text2Image.from_bbcode_text(
        "Tip：[b]发送序号[/b] 选择歌曲",
        30,
        align="center",
        fill=(255, 255, 255),
        fontname=config.ncm_list_font or "",
    )


    width = table_img.width + pic_padding * 2 + table_padding * 2
    height = (
        table_img.height
        + title_txt.height
        + tip_txt.height
        + table_padding * 7
    )

    bg = BACKGROUND.copy().convert("RGBA").resize((width, height), keep_ratio=True)
    #bg = bg.filter(ImageFilter.GaussianBlur(radius=5))
    y_offset = table_padding

    title_txt.draw_on_image(bg.image, ((width - title_txt.width) // 2, y_offset))
    y_offset += title_txt.height + table_padding

    tip_txt.draw_on_image(bg.image, ((width - tip_txt.width) // 2, y_offset))
    y_offset += tip_txt.height + table_padding

    bg.paste(
        (
            BuildImage.new(
                "RGBA",
                (
                    table_img.width + table_padding * 2,
                    table_img.height + table_padding * 2,
                ),
                (255, 255, 255, 50),
            ).circle_corner(table_border_radius)
        ),
        (pic_padding, y_offset),
        alpha=True,
    )
    y_offset += table_padding

    bg.paste(table_img, (pic_padding + table_padding, y_offset), alpha=True)
    y_offset += table_img.height + table_padding * 2


    return bg.save_jpg((0, 0, 0)).getvalue()

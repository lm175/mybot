from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="跑跑社团答题",
    description="超时空跑跑社团答题助手",
    usage=(
        "发送“/跑跑答题”进入答题模式\n"
        "   答题模式下可发送题目关键词进行搜索\n"
        " \n"
        "发送“q”退出答题模式"
    )
)


from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot import get_driver

from pathlib import Path
file_path = Path(__file__).parent

import sqlite3

conn = sqlite3.connect(file_path / 'club.db')
cursor = conn.cursor()



club_questions = on_fullmatch(("跑跑答题", "/跑跑答题"),  priority=10, block=True)

@club_questions.handle()
async def _():
    await club_questions.send("进入社团答题模式，发送“q”退出")

@club_questions.receive()
async def _(event: MessageEvent):
    question = event.get_plaintext()
    cancle = ["q", "quit"]
    if question in cancle:
        await club_questions.finish("答题结束")
    cursor.execute("""
        select question, answer from questions
                   where question like ?
    """, (f"%{question}%",))

    msg = ""
    results = cursor.fetchall()
    if results:
        for row in results:
            msg += f"题目: {row[0]}\n"
            msg += f"答案: {row[1]}\n\n"
    else:
        msg += f"未找到与关键词 '{question}' 相关的记录"
    await club_questions.reject(msg)



driver = get_driver()

@driver.on_shutdown
async def _():
    conn.close()
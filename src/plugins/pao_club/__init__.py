from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="跑跑社团答题",
    description="超时空跑跑社团答题助手",
    usage=(
        "/跑跑答题\n"
        "   介绍: 进入答题模式，答题模式下可发送题目关键词进行搜索\n"
        "   发送“q”退出答题模式\n"
        " \n"
        "/跑跑上传题库\n"
        "   私聊发送“/跑跑上传题库”后发送题库文件即可\n"
        "   支持的文件格式: xlsx、txt、json、db\n"
        "   发送“/跑跑题库格式”查看具体文件格式"
    ),
    extra={
        "notice": "不要上传错误答案\n上传有记录，乱传的会拉黑",
    },
)


from nonebot import on_fullmatch, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment
)
from nonebot import get_driver
from nonebot.log import logger

from pathlib import Path
import asyncio, json

from .db import DatabaseManager
from .utils import get_file_data
from .errors import *



club_questions = on_fullmatch(("跑跑答题", "/跑跑答题"),  priority=10, block=True)

@club_questions.handle()
async def _():
    await club_questions.send("进入社团答题模式，发送“q”退出")

@club_questions.receive()
async def _(event: MessageEvent):
    keyword = event.get_plaintext()
    if not keyword:
        await club_questions.reject()
    cancle = ["q", "quit"]
    if keyword in cancle:
        await club_questions.finish("答题结束")
    msg = await DatabaseManager.query(keyword)
    await club_questions.reject(msg)



xlsx_img = Path(__file__).parent / "resources" / "xlsx.png"
txt_img = Path(__file__).parent / "resources" / "txt.png"
json_img = Path(__file__).parent / "resources" / "json.png"
db_img = Path(__file__).parent / "resources" / "db.png"


upload = on_command("跑跑上传题库",  priority=10, block=True)


@upload.handle()
async def _(event: MessageEvent):
    if not isinstance(event, PrivateMessageEvent):
        await upload.finish("暂不支持群聊上传，请发送私聊")
    await upload.send("请发送文件，格式参考如下")
    await upload.send(MessageSegment.node_custom(
        user_id=event.self_id,
        nickname="",
        content=Message(
            "xlsx: 需包含“题目”和“答案”列" + MessageSegment.image(xlsx_img)
        )
    ) + MessageSegment.node_custom(
        user_id=event.self_id,
        nickname="",
        content=Message(
            "txt: 每行开始应为“题目 ”或“答案 ”" + MessageSegment.image(txt_img)
        )
    ) + MessageSegment.node_custom(
        user_id=event.self_id,
        nickname="",
        content=Message(
            "json: 题目为键，答案为值" + MessageSegment.image(json_img)
        )
    ) + MessageSegment.node_custom(
        user_id=event.self_id,
        nickname="",
        content=Message(
            "db: 数据库中应包含下表" + MessageSegment.image(db_img)
        )
    ))

@upload.receive()
async def _(bot: Bot, event: PrivateMessageEvent):
    file_id: str = ""
    for segment in event.message:
        if segment.type == "file":
            file_id = segment.data.get("file_id", "")
            break

    try:
        file_data = await bot.call_api(
            api="get_file",
            file_id=file_id
        )
        file_path = Path(file_data["file"])
    except:
        await upload.finish("文件获取失败")

    
    try:
        data = await asyncio.to_thread(get_file_data, file_path)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        await upload.finish("文件获取失败")
    except UnsupportedFileTypeError:
        logger.error(f"Unsupported file type: {file_path}")
        await upload.finish("上传失败，仅支持xlsx、txt、json、db")
    except UnexpectedFormatValueError as e:
        logger.error(f"Unexpected format in file {file_path}: {e}")
        await upload.finish(f"文件格式错误: {e}")
    except json.JSONDecodeError:
        logger.error(f"JSON decode error in file {file_path}")
        await upload.finish("JSON文件解析失败，请检查内容")
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing file {file_path}: {e}")
        await upload.finish(str(e))
    

    count = await DatabaseManager.update(data, event.user_id)
    total = await DatabaseManager.get_count()
    await upload.finish(
        f"上传成功！\n"
        f"新增 {count} 道题目\n"
        f"当前题库题目总数: {total}"
    )
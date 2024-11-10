from nonebot import on_command, on_keyword
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from typing import List, Dict
from pathlib import Path
from random import choice


path = str(Path(__file__).parent / 'pictures' / 'xxdhz')

def load_image_files_info(directory: str) -> tuple[List[str], Dict[str, str]]:
    extensions = ['.jpg', '.jpeg', '.png', '.gif']
    filenames = []  # 文件名列表（不包含后缀）
    filename_to_extension = {}  # 文件名到后缀名的映射字典

    directory_path = Path(directory)
    for file in directory_path.iterdir():
        if file.is_file() and file.suffix.lower() in extensions:
            filename = file.stem
            filenames.append(filename)
            filename_to_extension[filename] = file.suffix[1:]

    return filenames, filename_to_extension

TEXT_LIST, FILENAME_TO_EXTENSION_DICT = load_image_files_info(path)

async def process(matcher: Matcher, text: str, extension: str = "") -> None:
    if extension:
        file_path = f"{path}/{text}.{extension}"
        await matcher.send(
            message=MessageSegment.image(file_path),
        )
    else:
        await matcher.send('获取图片失败')

def handler(text: str) -> T_Handler:
    async def handle(matcher: Matcher):
        extension = FILENAME_TO_EXTENSION_DICT.get(text, "")
        await process(matcher, text, extension)

    return handle

def create_matchers():
    for text in TEXT_LIST:
        matcher = on_command(text, priority=12)
        matcher.append_handler(handler(text))

    random_text_matcher = on_keyword({"星星的孩子", "自研大佬"}, priority=12)
    async def random_text_handler(matcher: Matcher):
        random_text = choice(TEXT_LIST)
        await process(matcher, random_text, FILENAME_TO_EXTENSION_DICT[random_text])

    random_text_matcher.append_handler(random_text_handler)

create_matchers()



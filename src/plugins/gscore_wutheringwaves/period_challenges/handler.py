from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .utils import DataFetcher, PeriodManager, PeriodInfo
from .generator import ImageHandler, ImageGenerator, TowerImageGenerator, SlashImageGenerator
from .error import PeriodNotFoundError

# 构造消息
async def construct_message(
        zh_name: str,
        period_id: str,
        period_data: 'PeriodInfo',
        pics: list[bytes]
    ) -> Message:

    msg = Message(MessageSegment.node_custom(
        user_id=2854196310,
        nickname="小助手",
        content=f"{zh_name}第{period_id}期\n" +
                f"开放时间：{period_data.begin.strftime('%Y-%m-%d')} " + 
                f"至 {period_data.end.strftime('%Y-%m-%d')}"
    ))

    for pic in pics:
        msg.append(MessageSegment.node_custom(
            user_id=2854196310,
            nickname="小助手",
            content=Message(MessageSegment.image(pic))
        ))
    
    msg.append(MessageSegment.node_custom(
        user_id=2854196310,
        nickname="小助手",
        content="数据来源：https://ww2.hakush.in/"
    ))
    return msg



next_challenge = on_command("ww下期", aliases={"鸣潮下期"}, priority=1, block=True)

@next_challenge.handle()
async def _(arg: Message = CommandArg()):
    if arg.extract_plain_text().strip() == "深塔":
        challenge_name = "tower"
        zh_name = "深塔"
    elif arg.extract_plain_text().strip() == "海墟":
        challenge_name = "slash"
        zh_name = "海墟"
    else:
        await next_challenge.finish()

    data_fetcher = DataFetcher(base_url='https://api.hakush.in/ww/data')
    period_manager = PeriodManager(fetcher=data_fetcher, endpoint=f'{challenge_name}.json')

    try:
        current_period_id = await period_manager.get_period_id()
        next_period_id = str(int(current_period_id) + 1)
        img_handler = ImageHandler()
        pics = await img_handler.get_images(challenge_name, next_period_id)

        next_period_data = await period_manager.get_period_data(next_period_id)
    except PeriodNotFoundError:
        await next_challenge.finish(f"{zh_name}第{next_period_id}期数据未找到，可能尚未发布。")

    msg = await construct_message(
        zh_name=zh_name,
        period_id=next_period_id,
        period_data=next_period_data,
        pics=pics
    )
    await next_challenge.send(msg)



rerender = on_command("ww重渲染", aliases={"wwrerender"}, priority=1, block=True)

@rerender.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    if len(args) != 2:
        await rerender.finish("用法：ww重渲染 <深塔/海墟> <期数>")
    
    challenge_map = {
        "深塔": "tower",
        "海墟": "slash"
    }
    if args[0] not in challenge_map:
        await rerender.finish("挑战类型错误，仅支持 深塔 或 海墟")
    
    challenge_name = challenge_map[args[0]]
    period_id = args[1]

    img_handler = ImageHandler()
    img_generator = TowerImageGenerator() if challenge_name == "tower" else SlashImageGenerator()

    pics = await img_generator.generate_images(period_id)
    await img_handler.save_images_to_local(challenge_name, period_id, pics)

    msg = Message(MessageSegment.node_custom(
        user_id=2854196310,
        nickname="小助手",
        content=f"{args[0]}第{period_id}期 重渲染完成"
    ))
    for pic in pics:
        msg.append(MessageSegment.node_custom(
            user_id=2854196310,
            nickname="小助手",
            content=Message(MessageSegment.image(pic))
        ))
    
    await rerender.send(msg)



challenge_info = on_command("1ww", priority=10, block=True)

@challenge_info.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    if len(args) != 2:
        await challenge_info.finish("用法：1ww <深塔/海墟> <期数>")
    challenge_map = {
        "深塔": "tower",
        "海墟": "slash"
    }
    if args[0] not in challenge_map:
        await challenge_info.finish("挑战类型错误，仅支持 深塔 或 海墟")
    
    zh_name = args[0]
    challenge_name = challenge_map[zh_name]
    period_id = args[1]
    
    data_fetcher = DataFetcher(base_url='https://api.hakush.in/ww/data')
    period_manager = PeriodManager(fetcher=data_fetcher, endpoint=f'{challenge_name}.json')
    try:
        period_data = await period_manager.get_period_data(period_id)
        img_handler = ImageHandler()
        pics = await img_handler.get_images(challenge_name, period_id)
    except PeriodNotFoundError:
        await challenge_info.finish(f"{zh_name}第{period_id}期数据未找到，可能尚未发布。")

    msg = await construct_message(
        zh_name=zh_name,
        period_id=period_id,
        period_data=period_data,
        pics=pics
    )
    await challenge_info.send(msg)

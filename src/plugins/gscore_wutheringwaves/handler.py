from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from .utils import DataFetcher, PeriodManager, get_images

next_tower = on_command("ww下期深塔", priority=1, block=True)

@next_tower.handle()
async def _():
    data_fetcher = DataFetcher(base_url='https://api.hakush.in/ww/data')
    period_manager = PeriodManager(fetcher=data_fetcher, endpoint='tower.json')

    current_period_id = await period_manager.get_period_id()
    next_period_id = str(int(current_period_id) + 1)
    pics = await get_images("tower", next_period_id)

    next_period_data = await period_manager.get_period_data(next_period_id)

    msg = Message(MessageSegment.node_custom(
        user_id=2854196310,
        nickname="小助手",
        content=f"深塔第{next_period_id}期\n" +
                f"开放时间：{next_period_data.begin.strftime('%Y-%m-%d')} " + 
                f"至 {next_period_data.end.strftime('%Y-%m-%d')}"
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
    await next_tower.send(msg)




next_slash = on_command("ww下期海墟", priority=1, block=True)

@next_slash.handle()
async def _():
    data_fetcher = DataFetcher(base_url='https://api.hakush.in/ww/data')
    period_manager = PeriodManager(fetcher=data_fetcher, endpoint='slash.json')

    current_period_id = await period_manager.get_period_id()
    next_period_id = str(int(current_period_id) + 1)
    pics = await get_images("slash", next_period_id)

    next_period_data = await period_manager.get_period_data(next_period_id)

    msg = Message(MessageSegment.node_custom(
        user_id=2854196310,
        nickname="小助手",
        content=f"海墟第{next_period_id}期\n" +
                f"开放时间：{next_period_data.begin.strftime('%Y-%m-%d')} " + 
                f"至 {next_period_data.end.strftime('%Y-%m-%d')}"
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
    await next_tower.send(msg)
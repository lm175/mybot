from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, MessageEvent, MessageSegment, unescape

from .data_source import t2p, m2p

__des__ = '文本、Markdown转图片'
__cmd__ = '''
text2pic/t2p {text}
md2pic/m2p {text}
'''.strip()
__short_cmd__ = 't2p、m2p'
__example__ = '''
t2p test
m2p $test$ test `test`
'''.strip()
__usage__ = f'{__des__}\nUsage:\n{__cmd__}\nExample:\n{__example__}'


text2pic = on_command('text2pic', aliases={'t2p'}, priority=12)
md2pic = on_command('md2pic', aliases={'markdown', 'm2p'}, priority=12)


@text2pic.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    msg = unescape(event.get_plaintext().strip())
    if not msg:
        await text2pic.finish()

    img = await t2p(msg)
    if img:
        await text2pic.finish(MessageSegment.image(img))


@md2pic.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    msg = unescape(event.get_plaintext().strip())
    if not msg:
        await md2pic.finish()

    img = await m2p(msg)
    if img:
        await md2pic.finish(MessageSegment.image(img))

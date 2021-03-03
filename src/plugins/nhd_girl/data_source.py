import numpy as np
from nonebot.adapters.cqhttp import Message, MessageSegment, MessageEvent


def get_reply(msg, event):
    if not msg:
        return None
    nickname = ''
    if isinstance(event, MessageEvent):
        nickname = event.sender.nickname
    if not nickname:
        return None
    if '求交往' in msg:
        return '你是个好人，这张好人卡请收下吧~'
    if '求约会' in msg:
        return np.random.choice(['才不要呢！约会什么的最讨厌了！',
                                 '好的{}，三分钟后来八舍楼下等我哦！'.format(nickname)],
                                p=np.array([0.8, 0.2]).ravel())
    if '我要米' in msg or '求米' in msg:
        return np.random.choice(['哼！人家才不知道什么叫米呢！',
                                 '呵呵，你们不知道，我跟马爷谈笑风生，你们这些求米的人啊，naive！'],
                                p=np.array([0.8, 0.2]).ravel())
    if '马爷' in msg:
        return Message([{'type': 'text', 'data': {'text': '你说的是'}},
                        {'type': 'at', 'data': {'qq': '365956210'}},
                        {'type': 'text', 'data': {'text': '吗？马爷可是永远的博士之光呢！NHD娘最喜欢他了！嗯嗯！'}}])
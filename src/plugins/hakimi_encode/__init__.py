from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="南北绿豆",
    description="奇奇怪怪的文字加密",
    usage=(
        "编码: 南北绿豆 <文本>\n"
        "解码: 豆绿北南 <编码文本>\n"
    )
)



codebook = ['齁', '哦', '噢', '喔', '咕', '咿', '嗯', '啊', '～', '哈', '！', '唔', '哼', '❤', '呃', '呼']
codebook_map = {ch: i for i, ch in enumerate(codebook)}

def encode(input_raw: str) -> str:
    """将 UTF-8 文本编码为由 codebook 字符组成的字符串"""
    b = input_raw.encode('utf-8')
    parts = []
    for byte in b:
        high = (byte >> 4) & 0x0F
        low = byte & 0x0F
        parts.append(codebook[high])
        parts.append(codebook[low])
    return ''.join(parts)

def decode(input_code: str) -> str:
    """将编码字符串解码回 UTF-8 文本。出现错误时抛出 ValueError，含中文提示。"""
    if len(input_code) % 2 != 0:
        raise ValueError("输入长度必须为偶数")
    bytes_out = []
    for i in range(0, len(input_code), 2):
        high = codebook_map.get(input_code[i])
        low = codebook_map.get(input_code[i+1])
        if high is None or low is None:
            raise ValueError("输入包含非法字符")
        bytes_out.append((high << 4) | low)
    ba = bytes(bytes_out)
    try:
        return ba.decode('utf-8')
    except UnicodeDecodeError:
        hexstr = ' '.join(f'{b:02x}' for b in bytes_out)
        raise ValueError("无法正确解码为UTF-8文本: " + hexstr)


from nonebot import on_command
from nonebot.params import CommandArg, ArgStr
from nonebot.adapters.onebot.v11 import Message
from nonebot.typing import T_State

hakimi_encode = on_command("南北绿豆", priority=5, block=True)
@hakimi_encode.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if text := arg.extract_plain_text().strip():
        state['text'] = text

@hakimi_encode.got('text', prompt="请输入要编码的文本")
async def _(text: str = ArgStr('text')):
    encoded_text = encode(text)
    await hakimi_encode.finish(f"编码结果:\n{encoded_text}")


hakimi_decode = on_command("豆绿北南", priority=5, block=True)
@hakimi_decode.handle()
async def _(state: T_State, arg: Message = CommandArg()):
    if code := arg.extract_plain_text().strip():
        state['code'] = code

@hakimi_decode.got('code', prompt="请输入要解码的文本")
async def _(code: str = ArgStr('code')):
    try:
        decoded_text = decode(code)
    except ValueError as e:
        await hakimi_decode.finish(f"解码失败: {e}")
    await hakimi_decode.finish(f"解码结果:\n{decoded_text}")
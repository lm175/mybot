from nonebot.plugin import on_message, on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.typing import T_State

from .utils import handle_message, get_chat_bot, get_random_picture
from .base import UserData, store
data_dir = store.get_plugin_data_dir()

from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="AI对话",
    description="AI聊天插件",
    usage=(
        "@桃子 <你要说的内容>\n"
        "   介绍：触发AI对话\n"
        "   示例：@桃子 早上好\n"
        " \n"
        "/切换设定\n"
        "   介绍：可自己设置它的人设\n"
        "   示例：/切换设定 你是一只小猫\n"
        " \n"
        "/clear\n"
        "   介绍：清除对话记忆和人设"
    ),
    extra={
        "notice": "每位用户的对话记录和人设不互通",
    },
)


morning = ["早上好", "早安"]
night = ["晚安"]


ai_matcher = on_message(rule=to_me(), priority=99)

@ai_matcher.handle()
async def _(event: MessageEvent):
    message = await handle_message(event)
    chatbot = get_chat_bot(event.get_user_id())
    reply = await chatbot.ask(message)
    await ai_matcher.send(reply)
    
    msgstr = event.message.extract_plain_text()
    if msgstr in morning:
        pictures = data_dir / "morning"
    elif msgstr in night:
        pictures = data_dir / "night"
    else:
        await ai_matcher.finish()
    pic = await get_random_picture(data_dir / pictures)
    if pic:
        await ai_matcher.send(MessageSegment.image(pic))



clear_memory = on_command("clear", rule=to_me(), priority=10, block=True)

@clear_memory.handle()
async def _(event: MessageEvent):
    user_id = event.get_user_id()
    chatbot = get_chat_bot(user_id)
    await chatbot.clear(user_id)
    await clear_memory.finish("欸...刚刚发生什么了？")



change_identity = on_command(
    "切换人设",
    aliases={"更换人设", "更改人设", "切换设定", "更换设定", "更改设定"},
    rule=to_me(),
    priority=15,
    block=True
)


@change_identity.handle()
async def _handel_first_recieve(event: MessageEvent, state: T_State, args: Message = CommandArg()):
    state["user_id"] = event.get_user_id()
    if text := args.extract_plain_text():
        state["identity"] = text


@change_identity.got("identity", prompt="请发送新的角色设定")
async def _handle(state: T_State):
    user_id = state.get("user_id")
    text = state.get("identity")
    text = f"(请按照下述内容进行角色扮演\n{text})"
    chatbot = get_chat_bot(user_id)
    await chatbot.changeidentity(user_id, text)
    await change_identity.finish("切换成功")



change_model = on_command(
    "切换模型",
    aliases={"更换模型", "更改模型"},
    rule=to_me(),
    priority=15,
    block=True
)


@change_model.handle()
async def handel_first_recieve(event: MessageEvent, state: T_State, args: Message = CommandArg()):
    state["user_id"] = event.get_user_id()
    if model_name := args.extract_plain_text():
        state["model"] = model_name


@change_model.got("model", prompt="请发送要切换的模型")
async def handle(state: T_State):
    user_id = state.get("user_id")
    model_name = state.get("model")
    user = UserData(user_id)
    models = user.get_all_models()
    if model_name not in models:
        await change_model.finish(f"切换失败，当前仅支持{models}")
    user.change_model(model_name)
    await change_model.finish(f"用户{user_id}的对话模型已切换为[{model_name}]")

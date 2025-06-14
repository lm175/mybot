from nonebot import require
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

data_file = store.get_plugin_data_file("whitelist.json")
white_list: list[int] = []


from nonebot import on_command, on_request, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    GroupRequestEvent,
    PrivateMessageEvent,
    GroupIncreaseNoticeEvent
)
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11.helpers import extract_numbers
from nonebot.permission import SUPERUSER
from nonebot.log import logger

group_invite = on_request()

@group_invite.handle()
async def _(bot: Bot, event: GroupRequestEvent):
    group_id = event.group_id
    user_id = event.user_id
    flag = event.flag

    if group_id not in white_list:
        # await bot.send_private_msg(
        #     user_id=user_id,
        #     message=f'是个陌生群聊呢，还是先跟管理员{super_user}说一下再邀请我吧(｡･ω･｡)'
        # )
        pass
    else:
        try:
            await bot.set_group_add_request(flag=flag, sub_type='invite', approve=True)
            logger.info(f"Auto-approved group invitation to group {group_id} from user {user_id}.")
            
        except Exception as e:
            logger.error(f"Failed to auto-approve group invitation: {e}")


async def INCchecker(event: GroupIncreaseNoticeEvent) -> bool:
    return True

inc = on_notice(rule=INCchecker)

@inc.handle()
async def _(bot: Bot, event: GroupIncreaseNoticeEvent):
    user_id = event.user_id
    if user_id == event.self_id and event.group_id not in white_list:
        try:
            await bot.set_group_leave(
                group_id=event.group_id
            )
        except Exception as e:
            logger.error(e)



async def invite_checker(event: PrivateMessageEvent) -> bool:
    text = str(event.message)
    if '"app":"com.tencent.qun.invite"' in text:
        return True
    return False


blocker = on_message(rule=invite_checker, priority=5, block=True)
@blocker.handle()
async def _():
    pass


append_group = on_command("添加群组", permission=SUPERUSER, priority=5, block=True)

@append_group.handle()
async def handle_add_whitelist(args: Message = CommandArg()):
    global white_list
    nums = extract_numbers(args)
    if nums:
        group_id = int(nums[0])
    else:
        await append_group.finish("参数错误")
    if group_id not in white_list:
        white_list.append(group_id)
        await append_group.finish(f"群组{group_id}已添加到白名单")
    else:
        await append_group.finish("该群已在白名单中，无需重复添加")



remove_group = on_command("移除群组", permission=SUPERUSER, priority=5, block=True)

@remove_group.handle()
async def handle_sub_whitelist(bot: Bot, args: Message = CommandArg()):
    global white_list
    nums = extract_numbers(args)
    if nums:
        group_id = int(nums[0])
    else:
        await append_group.finish("参数错误")
    
    if group_id in white_list:
        white_list.remove(group_id)
        await remove_group.send(f"群组{group_id}已从白名单移除")
        try:
            await bot.set_group_leave(group_id=group_id)
            await remove_group.send(f"已退出群{group_id}")
        except Exception as e:
            await remove_group.send(f"退出群组失败, 错误信息：{e}")
    else:
        await remove_group.finish("该群不在白名单中")




from nonebot import get_driver
import json

driver = get_driver()

@driver.on_startup
async def start():
    global white_list
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            white_list = json.load(f)
    except:
        white_list = []


@driver.on_shutdown
async def close():
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(white_list, f, ensure_ascii=False, indent=4)
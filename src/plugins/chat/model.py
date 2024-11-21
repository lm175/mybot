from nonebot.adapters.onebot.v11 import Message, MessageSegment

import asyncio, re
CHATLOCK = asyncio.Lock()

from .revGLM import glm
from .revTongYi import qianwen
from .config import config
from .base import BaseBot, UserData, ChatBotMessage


class GLM(BaseBot):
    chatbot = glm.ChatBot(Cookie=config.glm_cookie)
    _chatlock = asyncio.Lock()


    async def ask(self, message: ChatBotMessage) -> Message:
        records = message.user.records
        conversation_id = records.get("conversation_id")
        if conversation_id == None:
            conversation_id = ""
        async with self._chatlock:
            result, records["conversation_id"] = await asyncio.to_thread(self._ask, message, conversation_id)
            message.user.update_records(records)
            return result
    

    async def ask_directly(self, message: ChatBotMessage) -> Message:
        async with self._chatlock:
            result, conversation_id =  await asyncio.to_thread(self._ask, message)
            await asyncio.to_thread(self.chatbot.del_conversation, conversation_id)
            return result


    async def clear(self, user_id: str) -> bool:
        """切换为默认设定，删除聊天记录"""
        user = UserData(user_id)
        user.change_identity("default")
        records = user.records
        conversation_id = records["conversation_id"]
        records["conversation_id"] = ""
        user.update_records(records)
        async with self._chatlock:
            return await asyncio.to_thread(self.chatbot.del_conversation, conversation_id)
    

    async def changeidentity(self, user_id: str, text: str):
        user = UserData(user_id)
        await self.clear(user_id)
        user.change_identity(text)


    def _ask(self, message: ChatBotMessage, conversation_id: str = "") -> tuple[Message, str]:
        response = self.chatbot.ask(
            prompt=message.text,
            conversation_id=conversation_id,
            images=message.images
        )
        result = Message(response.content.lstrip())
        if response.image_url:
            result += MessageSegment.image(response.image_url)
        return result, response.conversation_id







class QWEN(BaseBot):
    chatbot = qianwen.Chatbot(cookies_str=config.qwen_cookie)
    _chatlock = asyncio.Lock()


    async def ask(self, message: ChatBotMessage) -> Message:
        records = message.user.records
        msgid = records.get("msgid")
        sessionid = records.get("sessionid")
        if msgid == None:
            msgid = ""
            sessionid = ""
        async with self._chatlock:
            result, records["msgid"], records["sessionid"] = await asyncio.to_thread(self._ask, message, msgid, sessionid)
            message.user.update_records(records)
            return result


    async def ask_directly(self, message: ChatBotMessage) -> Message:
        async with self._chatlock:
            result, _, sessionid =  await asyncio.to_thread(self._ask, message)
            await asyncio.to_thread(self._del_conversation, sessionid)
            return result


    async def clear(self, user_id: str) -> bool:
        """切换为默认设定，删除聊天记录"""
        user = UserData(user_id)
        user.change_identity("default")
        records = user.records
        sessionid = records.get("sessionid")
        records["msgid"] = ""
        records["sessionid"] = ""
        user.update_records(records)
        if sessionid:
            async with self._chatlock:
                return await asyncio.to_thread(self._del_conversation, sessionid)


    async def changeidentity(self, user_id: str, text: str):
        user = UserData(user_id)
        await self.clear(user_id)
        user.change_identity(text)


    def _ask(self, message: ChatBotMessage, msgid: str = "", sessionid: str = "") -> tuple[Message, str, str]:
        if message.images:
            response = self.chatbot.ask(
                prompt=message.text,
                parentId=msgid,
                sessionId=sessionid,
                image=message.images[0]
            )
        else:
            response = self.chatbot.ask(
                prompt=message.text,
                parentId=msgid,
                sessionId=sessionid,
            )
        text = response['contents'][0]['content']
        print(text)
        msg = self._transfer_msg(text)
        return msg, response["msgId"], response["sessionId"]
    

    def _transfer_msg(self, text: str) -> Message:
        url_pattern = r'\(https://wanx.alicdn.com/wanx/[^)]+'
        match = re.search(url_pattern, text)
        
        if match:
            start, end = match.span()

            part_before = text[:start].strip()  # 前半部分内容
            url = re.sub(r'\.png.*', '.png', match.group(0))[1:] # URL本身
            part_after = text[end:].strip()[1:]    # 后半部分内容
            
            return Message(part_before) + MessageSegment.image(url) + Message(part_after)
        else:
            return Message(text)


    def _del_conversation(self, sessionid: str) -> bool:
        return self.chatbot.delete_session(sessionId=sessionid)


glmbot = GLM()
qwenbot = QWEN()
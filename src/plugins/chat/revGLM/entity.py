class ChatContent:
    """对话内容"""
    content_type: str = ""
    content: str | list = ""
    image_url: str = ""

    def __init__(self, content: list[dict | None]) -> None:
        if content:
            self.content_type = content[0].get('type')
            self.content = content[0].get(self.content_type)

    @property
    def _image(self) -> str:
        if self.content:
            return self.content[0].get('image_url')
        return ""



class ChatResponse(ChatContent):
    """响应内容"""
    conversation_id: str

    def __init__(self, data: dict) -> None:
        self.conversation_id = data.get('conversation_id')
        self.__dict__ = data

        parts: list[dict] = data.get('parts')
        if parts:
            super().__init__(parts[0].get('content'))

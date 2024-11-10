# 一些常用的智能体，继承自ChatBot类，调用方法相同

from typing import Generator
from .entity import ChatResponse
from .glm import ChatBot


class ImageBot(ChatBot):
    """
    AI画图

    初始化参数:
    - Cookie: 你的Cookie
    - aspect_ratio: 图片的宽高比，支持的值有 '1:1', '4:3', '3:4'，默认为 '1:1'
    - style: 图片的风格，默认为 'none', 可选择的值包括：
        - 'none': 无特殊风格
        - 'photography': 摄影
        - 'ghibli': 吉卜力
        - 'van_gogh': 梵高
        - 'jap_anime': 日式动漫
        - 'watercolor': 水彩
        - 'cyberpunk': 赛博朋克
        - 'pixar': 皮克斯
        - 'da_vinci': 达芬奇
        - 'oil_painting': 油画
        - 'psychadelic': 多巴胺
        - 'line_art': 黑白线条
    """
    assistant_id = "65a232c082ff90a2ad2f15e2"
    
    def __init__(self, Cookie: str, aspect_ratio: str = "1:1", style: str = "none") -> None:
        super().__init__(Cookie)
        self.set_image_style(aspect_ratio, style)
    

    def set_image_style(self, aspect_ratio: str, style: str) -> None:
        self.meta_data['cogview'] = {"aspect_ratio": aspect_ratio, "style": style}
    
    def ask(
            self,
            prompt: str,
            conversation_id: str = "",
            timeout: int = 60,
            stream: bool = False,
            images: list[bytes] = None
    ) -> Generator[ChatResponse, None, None] | ChatResponse:
        prompt = f"{prompt} style: {self.meta_data.get('cogview').get('style')}"
        return super().ask(prompt, conversation_id, timeout, stream, images)



class SearchBot(ChatBot):
    """AI搜索"""
    assistant_id = "659e54b1b8006379b4b2abd6"

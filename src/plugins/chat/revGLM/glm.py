import requests, json, time, hashlib
from typing import Union, Generator, Any
from fake_useragent import UserAgent

from .data import ChatResponse, Content

class ChatBot:

    base_api = "https://chatglm.cn/chatglm"
    refresh_token: str

    assistant_id = "65940acff94777010aa6b796" # chatglm assistant
    meta_data: dict[str, Any] = {
        "if_plus_model": False,
        "plus_model_available": False
    }

    def __init__(self, Cookie: str) -> None:
        spt = Cookie.split(";")
        cookies = {}
        for it in spt:
            it = it.strip()
            if it:
                equ_loc = it.find("=")
                key = it[:equ_loc]
                value = it[equ_loc + 1:]
                cookies[key] = value
        self.refresh_token = cookies["chatglm_refresh_token"]

        self._access_token = None
        self._token_expiry = 0


    @property
    def access_token(self) -> str:
        current_time = time.time()
        if not self._access_token or current_time > self._token_expiry:
            refresh_url = f"{self.base_api}/user-api/user/refresh"
            md5_hash = hashlib.md5()
            md5_hash.update((str(current_time)).encode())
            headers = {
                "Content-Type": "application/json;charset=utf-8",
                "App-Name": "chatglm",
                "Authorization": f"Bearer {self.refresh_token}",
                "X-Device-Id": md5_hash.hexdigest(),
                "X-App-Platform": "pc",
                "X-App-Version": "0.0.1",
                "X-Request-Id": "",
                "X-Exp-Groups": "",
            }
            response = requests.post(refresh_url, headers=headers)
            print(response.text)
            if response.status_code == 200:
                self._access_token = f"Bearer {response.json().get('result').get('access_token')}"
                self._token_expiry = current_time + 1800    # 间隔半小时以上时刷新验证令牌
            else:
                raise Exception("Failed to refresh access token")

        return self._access_token

    @property
    def headers(self) -> dict:
        return {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "App-Name": "chatglm",
            "Authorization": self.access_token,
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://chatglm.cn",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": UserAgent().chrome,
            "X-App-Platform": "pc",
            "X-App-Version": "0.0.1",
            "X-Lang": "zh",
            "accept": "text/event-stream",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }
    

    def _stream_ask(
            self,
            prompt: str,
            conversation_id: str = "",
            timeout: int = 60,
            images: list[bytes] = []
    ) -> Generator[ChatResponse, None, None]:

        content: list[dict[str, str | list]] = [{"type": "text", "text": prompt}]
        if images:
            images_data = []
            for img in images:
                images_data.append(self._upload_image(img))
            content.append({"type": "image", "image": images_data})
            
        data = {
            "assistant_id": self.assistant_id,
            "conversation_id": conversation_id,
            "meta_data": self.meta_data,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }

        resp = requests.post(
            url=f"{self.base_api}/backend-api/assistant/stream",
            headers=self.headers,
            json=data,
            timeout=timeout,
            stream=True
        )

        if resp.status_code == 200:
            for line in resp.iter_lines():
                chunk = line.decode('utf-8')
                if chunk:
                    chunk = str(chunk).strip()
                    if chunk == "event:message":
                        continue
                    chunk = chunk[6:]
                    data = json.loads(chunk)
                    
                    result = ChatResponse(**data)
                    yield result
        else:
            raise Exception(resp.text)

    def _non_stream_ask(
            self,
            prompt: str,
            conversation_id: str = "",
            timeout: int = 60,
            images: list[bytes] = []
    ) -> ChatResponse:
        
        result = ChatResponse()
        image_url = ''
        for resp in self._stream_ask(
                prompt,
                conversation_id,
                timeout,
                images
        ):
            result = resp
            if result.image_url:
                image_url = result.image_url
        result.image_url = image_url
        return result


    def ask(
            self,
            prompt: str,
            conversation_id: str = "",
            timeout: int = 60,
            stream: bool = False,
            images: list[bytes] = []
    ) -> Union[Generator[ChatResponse, None, None], ChatResponse]:
        """提问

        Args:
            prompt (str): 提问内容
            conversation_id (str, optional): 对话id. Defaults to "".
            timeout (int, optional): 超时时间. Defaults to 60.
            stream (bool, optional): 是否流式. Defaults to False.
            images (bytes, optional): 图片二进制数据列表. Defaults to None.
        """

        if stream:
            return self._stream_ask(
                prompt,
                conversation_id,
                timeout,
                images
            )
        else:
            return self._non_stream_ask(
                prompt,
                conversation_id,
                timeout,
                images
            )
    

    def get_conversations(self) -> list:
        params = {
            "assistant_id": self.assistant_id,
            "page": 1,
            "page_size": 25
        }
        resp = requests.get(
            url=f"{self.base_api}/backend-api/assistant/conversation/list",
            params=params,
            headers=self.headers
        )
        return resp.json().get('result').get('conversation_list')
    

    def del_conversation(self, conversation_id: str) -> bool:
        """删除指定对话，参数为对话的conversation_id"""
        data = {
            "assistant_id": self.assistant_id,
            "conversation_id": conversation_id
        }
        resp = requests.post(
            f"{self.base_api}/backend-api/assistant/conversation/delete",
            headers=self.headers,
            json=data
        )
        if resp.status_code == 200:
            return True
        else:
            return False
        

    def _upload_image(self, image: bytes) -> dict:
        headers = {
            "Accept": "application/json, text/plain, */*",  
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",  
            "App-Name": "chatglm",  
            "Authorization": self.access_token,  
            "Connection": "keep-alive",  
            "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryMUeqfULMYn0q11JZ",
            "Origin": "https://chatglm.cn",  
            "User-Agent": UserAgent().chrome,  
            "X-App-Platform": "pc",  
            "X-App-Version": "0.0.1",  
            "X-Lang": "zh",  
        }

        filename = str(time.time()).replace('.', '')
        boundary = '----WebKitFormBoundaryMUeqfULMYn0q11JZ' # 构造文件表单数据
        data = (
            b'--' + boundary.encode('latin-1') + b'\r\n'
            b'Content-Disposition: form-data; name="file"; '
            b'filename="' + filename.encode('latin-1') + b'"\r\n'
            b'Content-Type: image/png\r\n\r\n'
            + image
            + b'\r\n'
            b'--' + boundary.encode('latin-1') + b'--\r\n'
        )
        response = requests.post(f"{self.base_api}/backend-api/assistant/file_upload", headers=headers, data=data)
        image_data = response.json().get('result')
        image_data['image_url'] = image_data.get('file_url')
        return image_data


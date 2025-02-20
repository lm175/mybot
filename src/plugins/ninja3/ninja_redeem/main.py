import json

from ddddocr import DdddOcr
import requests

from .api_client import Headers
from .error import APIError

class CaptchasHelper:
    base_url = 'https://captcha.pandadastudio.com'

    @classmethod
    def pass_captcha(cls):
        """执行一次验证，返回用于兑换请求的token"""
        res, token = cls.__do_pass_captcha()
        while res['code'] != 0:
            res, token = cls.__do_pass_captcha()
        return token
    
    @classmethod
    def __do_pass_captcha(cls):
        captchas_data = cls.captchas()
        # 获取验证图片
        bg_bytes = requests.get(captchas_data['data']['bgUrl']).content
        fg_bytes = requests.get(captchas_data['data']['fgUrl']).content
        # 识图
        det = DdddOcr(ocr=False, det=False, show_ad=False)
        position = det.slide_match(fg_bytes, bg_bytes, simple_target=True)
        result = cls.validate(captchas_data['data']['token'], position['target'][0])
        return result, captchas_data['data']['token']

    @classmethod
    def captchas(cls):
        """获取验证内容"""
        target_url = '/apis/v1/apps/ninja3/versions/v1/captchas'
        h = Headers()
        res = requests.get(
            url=f"{cls.base_url}{target_url}",
            headers=h.get_headers('GET', target_url)
        )
        if res.status_code != 200:
            raise APIError(f"HTTP {res.status_code}")
        return res.json()
    
    @classmethod
    def validate(cls, token: str, x: int):
        """发送验证请求"""
        target_url = f'/apis/v1/tokens/{token}/validate'
        h = Headers()
        res = requests.post(
            url=f'{cls.base_url}{target_url}',
            json={'x': x},
            headers=h.get_headers('POST', target_url, json.dumps({'x': x}))
        )
        if res.status_code != 200:
            raise APIError(f"HTTP {res.status_code}")
        return res.json()


def redeem_code(uid: int, code: str):
    """发送兑换请求
    - uid: 游戏uid
    - code: 兑换码
    """
    token = CaptchasHelper.pass_captcha()
    return requests.get(
        url='https://statistics.pandadastudio.com/player/giftCode',
        params={
            'uid': uid,
            'code': code,
            'token': token
        }
    )
import copy
from pathlib import Path

import execjs

from .utils import generate_x_yh_date, generate_x_yh_nonce_traceid

class Headers:

    ctx = execjs.compile(open(Path(__file__).parent / 'sign.js', encoding='utf-8').read())

    _headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-type": "application/json; charset=utf-8",
        "Origin": "https://statistics.pandadastudio.com",
        "Referer": "https://statistics.pandadastudio.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Microsoft Edge\";v=\"133\", \"Chromium\";v=\"133\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }

    def __init__(self):
        self.x_yh_appid = '356959'
        self.x_yh_date = generate_x_yh_date()
        self.x_yh_nonce = generate_x_yh_nonce_traceid()
        self.x_yh_traceid = generate_x_yh_nonce_traceid()

    def get_headers(self, method: str, url: str, x: str = '') -> dict[str, str]:
        h = copy.deepcopy(self._headers)
        h['x-yh-appid'] = self.x_yh_appid
        h['x-yh-date'] = self.x_yh_date
        h['x-yh-nonce'] = self.x_yh_nonce
        h['x-yh-traceid'] = self.x_yh_traceid
        h['Authorization'] = self.get_authorization(method, url, x)
        return h

    def get_authorization(self, method: str, url: str, x: str = '') -> str:
        e = (
            f"{method}\n"
            "captcha.pandadastudio.com\n"
            f"{url}\n"
            "\n"
            f"x-yh-appid:{self.x_yh_appid}\n"
            f"x-yh-date:{self.x_yh_date}\n"
            f"x-yh-nonce:{self.x_yh_nonce}\n"
            f"x-yh-traceid:{self.x_yh_traceid}"
        )
        return self.ctx.call('getAuthorization', e, x)
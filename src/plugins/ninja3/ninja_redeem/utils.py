from datetime import datetime, timezone
import secrets, struct

import requests

class WordArray:
    def __init__(self, words, sig_bytes):
        self.words = words  # 整形数组
        self.sig_bytes = sig_bytes  # 有效字节数
        self._map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="  # 映射表

    def clamp(self):
        """确保超出有效字节范围的部分被正确截断"""
        n = self.sig_bytes
        if n % 4:
            self.words[n // 4] &= 0xFFFFFFFF << (32 - n % 4 * 8)
        self.words = self.words[:-(n // 4 + 1):-1][::-1] + self.words[(n + 3) // 4:]

    def to_string(self):
        """将整形数组转换为Base64字符串"""
        self.clamp()
        t = self.words
        n = self.sig_bytes
        r = self._map
        o = []

        for i in range(0, n, 3):
            # 提取三个字节并合并成一个24位整数
            a = ((t[i >> 2] >> (24 - i % 4 * 8)) & 0xFF) << 16
            if i + 1 < len(t) * 4:
                a |= ((t[(i + 1) >> 2] >> (24 - (i + 1) % 4 * 8)) & 0xFF) << 8
            if i + 2 < len(t) * 4:
                a |= (t[(i + 2) >> 2] >> (24 - (i + 2) % 4 * 8)) & 0xFF

            # 将24位整数转换为四个6位段，并根据_map查找对应的字符
            for c in range(4):
                if i + 0.75 * c < n:
                    o.append(r[a >> (6 * (3 - c)) & 0x3F])

        # 添加填充字符
        u = r[64]
        while len(o) % 4:
            o.append(u)

        return ''.join(o)




def random_word_array(length_in_bytes) -> WordArray:
    if length_in_bytes % 4 != 0:
        raise ValueError('Length must be a multiple of 4.')
    random_bytes = secrets.token_bytes(length_in_bytes)
    words = list(struct.unpack(f"{length_in_bytes // 4}I", random_bytes))
    return WordArray(words, length_in_bytes)


def generate_x_yh_nonce_traceid() -> str:
    return random_word_array(16).to_string()


def generate_x_yh_date() -> str:
    current_time = datetime.now(timezone.utc)
    return current_time.strftime('%Y%m%dT%H%M%S') + 'Z'


def query_uid(uid: int) -> str | None:
    res = requests.get(f"https://statistics.pandadastudio.com/player/simpleInfo?uid={uid}")
    data: dict = res.json().get('data', {})
    if not data:
        return None
    
    return (
        f"uid: {data.get('uid', 0)}\n"
        f"{data.get('name', '')} - {data.get('serverId', 0) + 1}服 - {data.get('title', '')}"
    )
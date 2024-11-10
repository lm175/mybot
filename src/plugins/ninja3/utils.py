from selenium.webdriver import Edge
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from ddddocr import DdddOcr
from nonebot.log import logger

from io import BytesIO
import time, base64, json
from PIL import Image
from httpx import AsyncClient
import requests

from pathlib import Path
DATA_PATH = Path(__file__).parent / "data"
DHM = DATA_PATH / "bzdhm.txt"
QQ_TO_UID = DATA_PATH / "qq_to_uid.json"
FORBIDDEN = DATA_PATH / "forbidden.json"

class RedeemCode():
    def __init__(self, dhm: str) -> None:
        self.dhm=dhm
        self.driver=self.creat_driver()
    
    @classmethod
    def creat_driver(cls) -> Edge:
        options = Options()
        options.add_argument('--headless')
        driver = Edge(options=options)
        driver.implicitly_wait(2)
        driver.get("https://statistics.pandadastudio.com/")
        driver.set_window_size(1920, 1021)
        return driver


    def dhm_checker(self) -> bool:
        tip_text, _ = self.redeem_for_user("634431781")
        if tip_text == "领取失败，无效的礼包码" or tip_text == "领取失败，礼包码已过期":
            return False
        return True


    def redeem_for_user(self, uid: str) -> tuple[str, BytesIO]:
        """执行一次兑换，返回提示信息和截图"""
        driver = self.driver

        uid_input = driver.find_element(By.ID, "uid")
        uid_input.clear()
        uid_input.send_keys(uid)
        time.sleep(0.2)
        dhm_input = driver.find_element(By.ID, "dhm")
        dhm_input.clear()
        dhm_input.send_keys(self.dhm)

        submit = driver.find_element(By.CLASS_NAME, "submit")
        submit.click()

        self._pass_captcha(50)
        while True:
            try:
                tip_msg = driver.find_element(By.CLASS_NAME, "tip-msg").text
                time.sleep(0.2)
                screenshot = driver.get_screenshot_as_png()
                screenshot_stream = BytesIO(screenshot)
                image = Image.open(screenshot_stream)
                image = image.crop((0, 0, 2000, 1109))
                output = BytesIO()
                image.save(output, format='PNG')

                confirm = driver.find_element(By.CLASS_NAME, "confirm")
                confirm.click()
                return tip_msg, output
            except:
                self._pass_captcha(60)


    def _pass_captcha(self, fix: int):
        driver = self.driver
        time.sleep(1)
        try:
            # 碎片
            sp_element = driver.find_element(By.CLASS_NAME, "dx-captcha-body-slider")
            image_url = sp_element.get_attribute("src")
            if not image_url:
                return
            res = requests.get(image_url)
            sp_bytes = res.content

            # 背景
            bg_element = driver.find_element(By.CLASS_NAME, "dx-captcha-body")
            bg_BytesIo = BytesIO(base64.b64decode(bg_element.screenshot_as_base64))
            bg_image = Image.open(bg_BytesIo)
            bg_image = bg_image.crop((60, 0, 300, 150))
            bg_BytesIo = BytesIO()
            bg_image.save(bg_BytesIo, "PNG")

            # 识图
            det = DdddOcr(ocr=False, det=False, show_ad=False)
            position = det.slide_match(sp_bytes, bg_BytesIo.getvalue(), simple_target=True)
            value = position['target'][0] + fix

            # 滑块
            slider = driver.find_element(By.CLASS_NAME, "dx-captcha-bar-slider")
            action = ActionChains(driver)
            action.click_and_hold(slider).perform()
            action.move_by_offset(value, 0)
            action.release().perform()
        except Exception as e:
            logger.error(e)
            return


async def serch_uid(uid: int) -> str | None:
    async with AsyncClient() as client:
        res = await client.get(f"https://statistics.pandadastudio.com/player/simpleInfo?uid={uid}")
    data: dict = res.json().get('data')
    if not data:
        return None
    
    return f"uid: {data.get('uid')}\n{data.get('name')} - {data.get('serverId') + 1}服 - {data.get('title')}"



class UidData():
    """
    将QQ号到uid列表的字典数据封装成类
    可创建对象进行数据操作
    """
    def __init__(self, data: dict[str, list[int]]) -> None:
        self.data = data
    
    def get_users_uid(self, qq: str) -> list[int]:
        """返回指定qq号的所有uid"""
        if not self.data.get(qq):
            self.data[qq] = []
        return self.data.get(qq)

    def get_all_uids(self):
        """返回所有uid"""
        uid_list = [uid for value in self.data.values() for uid in value]
        return uid_list
    
    def get_qq_from_uid(self, uid: int) -> str:
        """获取uid所对应的qq号"""
        for k, v in self.data.items():
            if uid in v:
                return k
    
    def split_list(self):
        """将自身数据拆分成两组从qq到uid列表的映射"""
        sorted_items  = sorted(self.data.items(), key=lambda item: len(item[1]))  # 根据列表长度排序
        n = len(self.data) // 2 + 1
        return (dict(sorted_items[:n]), dict(sorted_items[n:]))

    def add_uid(self, qq: str, uid: int) -> None:
        uid_list = self.get_users_uid(qq)
        uid_list.append(uid)
        self.data[qq] = uid_list
    
    def del_uid(self, qq: str, uid: int) -> None:
        uid_list = self.get_users_uid(qq)
        uid_list.remove(uid)
        if uid_list:
            self.data[qq] = uid_list
        else:
            del self.data[qq]
        self.data = dict(sorted(self.data.items(), key=lambda item: len(item[1])))




def load_from_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_to_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_to_txt(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)
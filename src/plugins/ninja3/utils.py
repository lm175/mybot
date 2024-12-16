from selenium.webdriver import Edge
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from ddddocr import DdddOcr
from nonebot.log import logger

from io import BytesIO
from collections.abc import Iterable
import time, base64, json, datetime

from PIL import Image
from httpx import AsyncClient
from aiosqlite import Row
import requests



def split_list(users: Iterable[Row]) -> tuple[list[Row], list[Row]]:
    # 贪心算法，将users列表分成两半
    list1: list[Row] = []
    list2: list[Row] = []

    for usr in users:
        sum1 = sum(u[1] for u in list1)
        sum2 = sum(u[1] for u in list2)
        if sum1 <= sum2:
            list1.append(usr)
        else:
            list2.append(usr)
    
    return (list1, list2)


def is_this_week(date: datetime.date) -> bool:
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)

    return start_of_week <= date <= end_of_week



class RedeemCode():
    def __init__(self, code: str) -> None:
        self.code=code
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
        while tip_text == "领取失败，Internal Server Error":
            return self.dhm_checker()
        if tip_text == "领取失败，无效的礼包码":
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
        dhm_input.send_keys(self.code)

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
                if tip_msg == "领取失败，Internal Server Error":
                    return self.redeem_for_user(uid=uid)
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

async def serch_uid(uid: int) -> str:
    async with AsyncClient() as client:
        res = await client.get(f"https://statistics.pandadastudio.com/player/simpleInfo?uid={uid}")
    data: dict[str, str] = res.json().get('data')
    if not data:
        return ""
    
    if not data["title"]:
        data["title"] = "禁忍"
    return f"uid: {data['uid']}\n{data['name']} - {int(data['serverId']) + 1}服 - {data['title']}"

def load_from_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_to_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
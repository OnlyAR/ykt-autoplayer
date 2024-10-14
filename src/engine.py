import json
import re
import time

import requests

from loguru import logger
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

import config


class Engine:
    def __init__(self, base_url, show_browser: bool = True):
        self.show_browser = show_browser
        self.base_url = base_url
        self.home_url = base_url + "pro/portal/home/"
        self.course_url = base_url + "pro/courselist"

        options = webdriver.ChromeOptions()
        if not show_browser:
            options.add_argument("--headless")

        service = Service("../driver/chromedriver")
        self.driver = webdriver.Chrome(options=options, service=service)

        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win64",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

    def login(self, auto: bool = False, timeout: int = 60):
        self.driver.get(self.home_url)
        cookie_path = config.root_path / "data" / "cookies.json"
        if auto:
            if not cookie_path.exists():
                msg = "未找到cookie文件，请先手动登录后，再执行程序"
                logger.error(msg)
                raise ValueError(msg)

            cookies = json.loads(cookie_path.read_text())
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            logger.info("已加载cookie文件，5s后自动登录...")
            self.driver.get(self.course_url)
        else:
            try:
                WebDriverWait(self.driver, timeout).until(EC.url_to_be(self.course_url))
                logger.info("登录成功，已经跳转到目标网页：" + self.course_url)

                cookies = self.driver.get_cookies()
                cookie_path.parent.mkdir(parents=True, exist_ok=True)
                cookie_path.write_text(json.dumps(cookies))
                logger.info("已保存cookie到文件：" + str(cookie_path))
            except TimeoutException:
                logger.error("登录超时")
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        logger.info("页面加载完成")

    def api_list_courses(self) -> list[dict]:
        url = self.base_url + "mooc-api/v1/lms/user/user-courses/"
        params = {
            "status": 1,
            "page": 1,
            "no_page": 1,
            "term": "latest",
            "uv_id": config.university_id,
        }

        cookies = {d["name"]: d["value"] for d in self.driver.get_cookies()}
        required_headers = ["platform-id", "university-id", "xtbz"]
        headers = {
            k: cookies[k.replace("-", "_")] for k in required_headers
        }
        response = requests.get(url, params=params, cookies=cookies, headers=headers).json()
        product_list = response["data"]["product_list"]
        return [
            {
                "sku_id": product["sku_id"],
                "course_name": product["course_name"],
                "course_sign": product["course_sign"],
                "classroom_id": product["classroom_id"],
                "course_id": product["course_id"],
            } for product in product_list
        ]

    def api_get_course_contents(self, course_info: dict) -> dict:
        """
        https://buaa.yuketang.cn/pro/lms/Baa8BNvtpbN/23421335/studycontent
        """
        url = self.base_url + "mooc-api/v1/lms/learn/course/chapter"
        params = {
            "cid": course_info["classroom_id"],
            "sign": course_info["course_sign"],
            "term": "latest",
            "uv_id": config.university_id
        }
        cookies = {d["name"]: d["value"] for d in self.driver.get_cookies()}
        required_headers = ["platform-id", "university-id", "xtbz"]
        headers = {
            k: cookies[k.replace("-", "_")] for k in required_headers
        }
        return requests.get(url, params=params, cookies=cookies, headers=headers).json()

    def get_course_contents(self, course_info: dict, timeout: int = 60) -> dict:
        url = self.base_url + f"pro/lms/{course_info['course_sign']}/{course_info['classroom_id']}/studycontent"
        self.driver.get(url)

        target_class = "el-tooltip leaf-detail"
        WebDriverWait(self.driver, timeout).until(
            lambda driver: len(driver.find_elements(By.XPATH, f'//div[@class="{target_class}"]')) > 0
        )
        time.sleep(0.5)
        divs = self.driver.find_elements(By.XPATH, f'//div[@class="{target_class}"]')
        status_dict = {}
        for div in divs:
            div1, div2 = div.find_elements(By.XPATH, "div")
            title = div1.find_element(By.TAG_NAME, "span").text
            status = div2.find_element(By.XPATH, "div/div").text
            status_dict[title] = status
        return status_dict

    def get_course_details(self, course_info: dict) -> list[dict]:
        contents = self.api_get_course_contents(course_info)
        status_dict = self.get_course_contents(course_info)
        details = []
        type_dict = {0: "video", 6: "homework", 5: "exam"}
        for chapter in contents["data"]["course_chapter"]:
            for section in chapter["section_leaf_list"]:
                if "exam" in section:
                    details.append({
                        "name": section["name"],
                        "type": type_dict[section["leaf_type"]],
                        "status": status_dict[section["name"]]
                    })
                    continue
                for leaf in section["leaf_list"]:
                    url = self.base_url + f"pro/lms/{course_info['course_sign']}/{course_info['classroom_id']}/{type_dict[leaf['leaf_type']]}/{leaf['id']}"
                    details.append({
                        "name": leaf["name"],
                        "url": url,
                        "status": status_dict[leaf["name"]],
                        "type": type_dict[leaf["leaf_type"]]
                    })
        return details

    def watch(self, url, timeout: int = 60):
        logger.info(f"正在观看：{url}")
        self.driver.get(url)
        duration_path = '//span[@class="text"]'
        while True:
            try:
                time.sleep(5)
                button = self.driver.find_element(By.XPATH, f'//*[@id="video-box"]/div/xt-wrap/xt-bigbutton/button')
                button.click()
                time.sleep(0.5)

                duration = self.driver.find_element(By.XPATH, duration_path).text
                logger.info("初始播放进度：" + duration)
                break
            except (NoSuchElementException, ElementNotInteractableException):
                logger.warning("找不到按钮，正在重试...")
                self.driver.refresh()

        while True:
            time.sleep(10)
            duration = self.driver.find_element(By.XPATH, duration_path).text
            logger.info(duration)
            pattern = re.compile(r"(\d+)")
            match = pattern.search(duration).group(1)
            if int(match) == 100:
                return

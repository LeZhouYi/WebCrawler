import base64
import os
import re
import shutil
import time
from typing import Optional, Union

from pywinauto import Desktop, Application
from selenium.webdriver.common import action_chains
from selenium.webdriver.remote.webelement import WebElement

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from typing_extensions import LiteralString

from core.common.crawl_utils import to_lower_str
from core.config.config import get_config_by_section
from core.log.logger import logger
from core.config.config import get_config


class WebCrawler:

    def __init__(self):
        self.driver = None  # 浏览器驱动
        self.webdriver_type = to_lower_str(get_config_by_section("webdriver", "browser_type"))  # 驱动类型
        self.download_path = os.path.join(os.getcwd(), get_config_by_section("webdriver", "download_path"))  # 设置浏览器下载路径
        self.will_save_photo = get_config("save_screenshot") == "True"
        os.makedirs(self.download_path, exist_ok=True)

    def init_webdriver(self):
        """初始化浏览器驱动"""
        if self.webdriver_type == "edge":
            self.init_edge_driver()
        elif self.webdriver_type == "chrome":
            self.init_chrome_driver()

    def init_chrome_driver(self):
        """初始化Chrome"""
        chrome_options = ChromeOptions()
        chrome_config = get_config_by_section("webdriver", self.webdriver_type)
        for argument in chrome_config["arguments"]:
            chrome_options.add_argument(argument)
        if chrome_config["remote"]:
            self.driver = webdriver.Remote(command_executor=chrome_config["remote_server"], options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

    def init_edge_driver(self):
        """初始化Edge"""
        edge_options = EdgeOptions()
        edge_config = get_config_by_section("webdriver", self.webdriver_type)
        for argument in edge_config["arguments"]:
            edge_options.add_argument(argument)
        edge_options.add_experimental_option("prefs", edge_config["prefs"])
        self.driver = webdriver.Edge(options=edge_options)
        if edge_config["remote"]:
            self.driver = webdriver.Remote(command_executor=edge_config["remote_server"], options=edge_options)
        else:
            self.driver = webdriver.Edge(options=edge_options)
        for cmd, cmd_args in edge_config["params"].items():
            self.driver.execute_cdp_cmd(cmd, cmd_args)

    def save_page(self, file_path: str, scale: float = 1.0):
        """
        保存网页为pdf
        :param file_path: 完整的本地文件路径
        :param scale: pdf缩放比例[0.1,2]
        """
        pdf_data = self.driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "displayHeaderFooter": False,
            "landscape": True,
            "scale": scale
        })
        with open(file_path, "wb") as file:
            file.write(base64.b64decode(pdf_data["data"]))

    def wait_download_file(self, filename: str, times: int = 30) -> bool:
        """等待下载文件"""
        des_file = self.format_download_file_name(filename)
        for _ in range(times):
            for file_name in os.listdir(self.download_path):
                format_name = self.format_download_file_name(file_name)
                if des_file.endswith(format_name) and not file_name.endswith(".crdownload"):
                    return True
            time.sleep(1)
        return False

    def move_download_file(self, des_file: str, des_path: str) -> bool:
        """
        移动下载好的文件到特定路径
        :param des_file: 目标文件名
        :param des_path: 目标路径
        :return: true->操作成功；False->找不到文件
        """
        des_file = self.format_download_file_name(des_file)
        for file_name in os.listdir(self.download_path):
            format_name = self.format_download_file_name(file_name)
            if des_file.endswith(format_name) and not file_name.endswith(".crdownload"):
                file_path = os.path.join(self.download_path, file_name)
                des_file_path = os.path.join(des_path, file_name)
                if os.path.exists(des_file_path):
                    os.remove(des_file_path)
                shutil.move(file_path, des_path)
                return True
        return False

    @staticmethod
    def format_download_file_name(filename: str):
        filename = filename.replace(" ", "")
        filename = filename.replace("+", "")
        filename = filename.replace(" ", "")
        return filename.split(".")[0]

    def wait_element(self, by: str, by_value: str, wait_time: int = 30) -> Optional[WebElement]:
        """
        等待某元素并返回
        :param by: 查找的类型
        :param by_value: 查找类型对应的关键数据
        :param wait_time: 等待最大时间/秒
        :return: 返回找到的页面元素或None
        """
        for i in range(int(wait_time / 0.5)):
            elements = self.driver.find_elements(by, by_value)
            if len(elements) > 0:
                return elements[0]
            time.sleep(0.5)
        raise ValueError("找不到元素:%s" % by_value)

    def wait_display_element(self, by: str, by_value: str, wait_time: int = 30) -> Optional[WebElement]:
        """
        等待某元素并返回
        :param by: 查找的类型
        :param by_value: 查找类型对应的关键数据
        :param wait_time: 等待最大时间/秒
        :return: 返回找到的页面元素或None
        """
        for i in range(int(wait_time / 0.5)):
            elements = self.driver.find_elements(by, by_value)
            if len(elements) > 0:
                try:
                    if elements[0].is_displayed():
                        return elements[0]
                except Exception as e:
                    print(e)
            time.sleep(0.5)
        raise ValueError("找不到元素:%s" % by_value)

    def click_element(self, by: str, value: str):
        """
        点击元素
        :param by: 查找的类型
        :param value: 查找类型对应的关键数据
        """
        element = self.driver.find_element(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        action_chains.ActionChains(self.driver).move_to_element(element).perform()
        self.driver.execute_script("arguments[0].click();", element)
        time.sleep(1)

    def click_element_by_element(self, element: WebElement):
        """点击元素"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        action_chains.ActionChains(self.driver).move_to_element(element).perform()
        self.driver.execute_script("arguments[0].click();", element)
        time.sleep(1)

    def click_input_element(self, element: WebElement, text: str):
        """
        点击元素并输入
        :param element: 要输入数据的页面元素
        :param text: 输入的内容
        """
        if text is None:
            return
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        action_chains.ActionChains(self.driver).click(element).perform()
        element.clear()
        element.send_keys(text)
        time.sleep(1)

    def exist_element(self, by: str, by_value: str) -> bool:
        """
        查看某元素是否存在
        :param by: 查找的类型
        :param by_value: 查找类型对应的关键数据
        """
        return len(self.driver.find_elements(by, by_value)) > 0

    def switch_latest_window(self):
        """切换至最新的窗"""
        windows = self.driver.window_handles
        if len(windows) > 1:
            self.driver.switch_to.window(windows[-1])

    def close_last_window(self):
        """清理最后一个窗口，若只有一个窗口时不处理"""
        windows = self.driver.window_handles
        if len(windows) > 1:
            self.driver.switch_to.window(windows[-1])
            self.driver.close()
            self.driver.switch_to.window(windows[-2])

    def clear_other_window(self):
        """清理除主窗口外的窗口"""
        windows = self.driver.window_handles
        if len(windows) > 1:
            for window in windows[1:]:
                try:
                    self.driver.switch_to.window(window)
                    self.driver.close()
                except Exception as e:
                    logger.warning("关闭窗口失败：%s" % e)
        self.driver.switch_to.window(windows[0])

    @staticmethod
    def get_open_file_handle(browser_pattern: str = r"^[\S\s]+Microsoft[\s\S]+Edge$", open_text: str = "打开"):
        """获取浏览器句柄"""
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        # 遍历所有窗口，打印窗口标题和句柄
        for window in windows:
            if re.match(browser_pattern, window.window_text()):
                app = Application(backend="uia").connect(handle=window.handle)
                main_browser = app.windows()[0]
                if len(main_browser.children(title=open_text)) > 0:
                    return window.handle
        return None

    @staticmethod
    def upload_file_by_window(handle, filepath: Union[LiteralString, str, bytes], open_text: str = "打开",
                              input_text: str = "文件名(N):", confirm_text: str = "打开(O)"):
        """通过浏览器上传文件"""
        app = Application(backend="uia").connect(handle=handle)
        main_browser = app.windows()[0]
        file_chooser = main_browser.children(title=open_text)[0]
        path_input = file_chooser.descendants(title=input_text, control_type="Edit")[0]
        # 输入文件
        path_input.set_text(filepath)
        open_button = file_chooser.descendants(title=confirm_text, control_type="Button")[0]
        open_button.click()

    def into_frame(self, by: str, frame_xpath: str, timeout: int = 30):
        """进入iframe"""
        WebDriverWait(self.driver, timeout).until(ec.frame_to_be_available_and_switch_to_it((by, frame_xpath)))

    @staticmethod
    def wait_child_element(parent_element: WebElement, by: str, by_value: str, wait_time: int = 30) -> Optional[
        WebElement]:
        """
        等待某元素并返回
        :param parent_element: 父元素
        :param by: 查找的类型
        :param by_value: 查找类型对应的关键数据
        :param wait_time: 等待最大时间/秒
        :return: 返回找到的页面元素或None
        """
        for i in range(int(wait_time / 0.5)):
            elements = parent_element.find_elements(by, by_value)
            if len(elements) > 0:
                try:
                    if elements[0].is_displayed():
                        return elements[0]
                except Exception as e:
                    print(e)
            time.sleep(0.5)
        raise ValueError("找不到元素:%s" % by_value)

    def full_load_scroll(self, scroll_element):
        """完全滚动到内容底部，使其内容完全加载"""
        check_script = """
                    var element = arguments[0];
                    return element.scrollTop + element.clientHeight >= element.scrollHeight;
                """
        scroll_script = """
                    var element = arguments[0];
                    element.scrollTop = element.scrollHeight - element.clientHeight;
                """
        for _ in range(20):
            self.driver.execute_script(scroll_script, scroll_element)
            time.sleep(2)
            is_to_bottom = self.driver.execute_script(check_script, scroll_element)
            if is_to_bottom:
                break

    def clear_download(self):
        """清理下载文件夹"""
        try:
            shutil.rmtree(self.download_path)
            os.makedirs(self.download_path, exist_ok=True)
        except Exception as e:
            logger.warning("清理下载文件夹失败:%s" % e)

    def save_screenshot(self, file_path: Union[os.PathLike, str], filename: str = None):
        """保存截图"""
        if not self.will_save_photo:
            return
        if not os.path.exists(file_path):
            os.makedirs(file_path, exist_ok=True)
        if filename is None:
            filename = "%s.png" % (int(time.time()))
            time.sleep(1)
        self.driver.save_screenshot(os.path.join(file_path, filename))

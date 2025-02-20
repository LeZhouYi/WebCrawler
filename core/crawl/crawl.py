import base64
import os
import re
import shutil
import time
from typing import Optional, Union
from urllib.parse import unquote

import requests
from pywinauto import Desktop, Application
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from selenium import webdriver
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from typing_extensions import LiteralString

from core.config.config import get_config
from core.log.logger import logger

class Crawler:

    def __init__(self):
        self.driver = None  # 浏览器驱动
        self.download_dir = None  # 下载文件夹
        self.webdriver_type = get_config("webdriver_type")  # 驱动类型

    def init_webdriver(self):
        """初始化浏览器驱动"""
        self.download_dir = os.path.join(os.getcwd(), get_config("download_dir"))
        assert os.path.exists(self.download_dir)
        if self.webdriver_type == "Edge":
            edge_options = EdgeOptions()
            if get_config("browser_gui_mode") == "nogui":
                edge_options.add_argument("--headless")  # 无窗口模式
            edge_options.add_argument("--disable-infobars")  # 禁用信息弹窗
            edge_options.add_argument("--disable-gpu")  # 禁用gpu加速
            edge_options.add_argument("--window-position=0,0")  # 浏览器位置
            edge_options.add_argument("--window-size=1920,1080")  # 浏览器大小
            edge_options.add_argument("--disable-notifications")
            edge_options.add_argument("--no-download-notification")
            edge_options.add_argument("--safebrowsing-disable-download-protection")
            edge_options.add_argument("--disable-software-rasterizer")
            # 添加实验性功能，用于设置下载路径
            prefs = {
                "browser": {
                    "show_hub_popup_on_download_start": False
                },
                "download": {
                    "default_directory": self.download_dir,
                    "prompt_for_download": False,
                    "directory_upgrade": True
                },
                "user_experience": {
                    "personalization_data_consent_enabled": True
                },
                "download.neverAsk.saveToDisk": "application/domain-of-my-app",
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.default_content_setting_values.notifications": 2,
                "profile.content_settings.pattern_pairs.*,*.multiple-automatic-downloads": 1
            }
            edge_options.add_experimental_option("prefs", prefs)
            # edge_options.add_experimental_option("excludeSwitches", ["disable-popup-blocking"])
            params = {
                "behavior": "allow",
                "downloadPath": self.download_dir
            }
            self.driver = webdriver.Edge(options=edge_options)
            self.driver.execute_cdp_cmd('Page.setDownloadBehavior', params)
            self.driver.set_page_load_timeout(120)
            self.driver.set_script_timeout(120)
            self.driver.implicitly_wait(30)
        elif self.webdriver_type == "Chrome":
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--start-fullscreen")  # 全屏
            if get_config("browser_gui_mode") == "nogui":
                chrome_options.add_argument("--headless")  # 无窗口模式
            # 设置下载路径
            chrome_options.add_experimental_option("prefs", {
                "download.default_directory": self.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            })
            chrome_options.add_argument("--disable-infobars")  # 禁用信息弹窗
            chrome_options.add_argument("--disable-gpu")  # 禁用gpu加速
            chrome_options.add_argument("--window-position=0,0")  # 浏览器位置
            chrome_options.add_argument("--window-size=1920,1080")  # 浏览器大小
            self.driver = webdriver.Chrome(options=chrome_options)

    @staticmethod
    def unquote_file_name(file_name: str) -> str:
        """
        将url编码格式的文件名转成当前系统合适的文件名
        :param file_name: 未编码的文件名
        :return: 编码转换后的文件名
        """
        return unquote(file_name)

    @staticmethod
    def download_file(url: str, file_path: Union[LiteralString, str, bytes]) -> bool:
        """
        下载文件到本地
        :param url: 文件链接
        :param file_path: 完整的本地文件路径
        :return: true->下载成功
        """
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return True
        return False

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
            for file_name in os.listdir(self.download_dir):
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
        for file_name in os.listdir(self.download_dir):
            format_name = self.format_download_file_name(file_name)
            if des_file.endswith(format_name) and not file_name.endswith(".crdownload"):
                file_path = os.path.join(self.download_dir, file_name)
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

    def click_element_by_index(self, by: str, value: str, index: int = 0):
        elements = self.driver.find_elements(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView();", elements[index])
        action_chains.ActionChains(self.driver).move_to_element(elements[index]).perform()
        self.driver.execute_script("arguments[0].click();", elements[index])
        time.sleep(1)

    def click_element_by_element(self, element: WebElement):
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
                    logger.warning("关闭窗口失败：%s"%e)
        self.driver.switch_to.window(windows[0])

    @staticmethod
    def get_open_file_handle(browser_pattern: str = r"^[\S\s]+Microsoft[\s\S]+Edge$"):
        """获取浏览器句柄"""
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        # 遍历所有窗口，打印窗口标题和句柄
        for window in windows:
            if re.match(browser_pattern, window.window_text()):
                # if str(window.window_text()).find("Microsoft​ Edge") > -1:
                app = Application(backend="uia").connect(handle=window.handle)
                main_browser = app.windows()[0]
                if len(main_browser.children(title="打开")) > 0:
                    return window.handle
        return None

    @staticmethod
    def upload_file_by_window(handle, filepath: Union[LiteralString, str, bytes]):
        """通过浏览器上传文件"""
        app = Application(backend="uia").connect(handle=handle)
        main_browser = app.windows()[0]
        file_chooser = main_browser.children(title="打开")[0]
        path_input = file_chooser.descendants(title="文件名(N):", control_type="Edit")[0]
        # 输入文件
        path_input.set_text(filepath)
        open_button = file_chooser.descendants(title="打开(O)", control_type="Button")[0]
        open_button.click()

    def into_frame_by_id(self, frame_id: str, timeout: int = 30):
        """进入iframe"""
        WebDriverWait(self.driver, timeout).until(ec.frame_to_be_available_and_switch_to_it((By.ID, frame_id)))

    def into_frame_by_name(self, frame_name: str, timeout: int = 30):
        """进入iframe"""
        WebDriverWait(self.driver, timeout).until(ec.frame_to_be_available_and_switch_to_it((By.NAME, frame_name)))

    @staticmethod
    def delete_file(filepath: Union[LiteralString, str, bytes]) -> bool:
        """删除本地文件"""
        try:
            os.remove(filepath)
            return True
        except OSError:
            return False

    @staticmethod
    def gen_download_script(url: str, filename: str) -> str:
        """生成下载文件的脚本"""
        return """
            async function downloadFile(fileUrl, filename){
                try{
                    const response = await fetch(fileUrl);
                    if (!response.ok){
                        throw new Error('FailDownload');
                    }
                    const blob = await response.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                } catch (error) {
                    console.error(error);
                }
            }
            const downloadUrl = '%s';
            const downloadName = '%s';
            downloadFile(downloadUrl, downloadName); 
        """ % (url, filename)

    @staticmethod
    def wait_child_element(parent_element: WebElement, by: str, by_value: str, wait_time: int = 30) -> Optional[WebElement]:
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

    @staticmethod
    def gen_url_download_script(url):
        return """
            const link = document.createElement('a');
            link.href = '%s';
            link.setAttribute('download', '');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        """%url
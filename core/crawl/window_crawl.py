import os
import re
import time
from typing import Union

import requests
from pywinauto import Desktop, Application
from typing_extensions import LiteralString

from core.config.config import get_config


class WindowCrawler:

    def __init__(self):
        self.download_dir = None  # 下载文件夹

    def init_window_crawler(self):
        self.download_dir = os.path.join(os.getcwd(), get_config("download_dir"))
        os.makedirs(self.download_dir, exist_ok=True)

    @staticmethod
    def find_child_elements(wrapper, title_pattern):
        """通过标题查找子元素"""
        elements = []
        for children in wrapper.descendants():
            if re.match(title_pattern, children.window_text()):
                elements.append(children)
        return elements

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

    @staticmethod
    def delete_file(filepath: Union[LiteralString, str, bytes]) -> bool:
        """删除本地文件"""
        try:
            os.remove(filepath)
            return True
        except OSError:
            return False

    @staticmethod
    def find_app_by_child_name(child_name: str):
        """通过窗口的子元素来匹配应用"""
        desktop = Desktop(backend="uia")
        app_window_handles = desktop.windows()
        for app_window_handle in app_window_handles:
            app = Application(backend="uia").connect(handle=app_window_handle.handle)
            for app_window in app.windows():
                if len(app_window.descendants(title=child_name)) > 0:
                    return app
        return None

    @staticmethod
    def wait_app_by_child_name(child_name: str, timeout: int = 30):
        """等待出现匹配的APP"""
        for _ in range(int(timeout / 6)):
            desktop = Desktop(backend="uia")
            app_window_handles = desktop.windows()
            for app_window_handle in app_window_handles:
                app = Application(backend="uia").connect(handle=app_window_handle.handle)
                for app_window in app.windows():
                    if len(app_window.descendants(title=child_name)) > 0:
                        return app
            time.sleep(5)
        raise Exception("找不到APP匹配子元素为 %s " % child_name)

    @staticmethod
    def find_child_window(app: Application, child_name: str):
        """查找子窗口"""
        for app_window in app.windows():
            if app_window.window_text() == child_name:
                return app_window
        return None

    @staticmethod
    def find_child_element_starts(app: Application, start_text: str):
        """以开头字符串匹配窗口"""
        for app_window in app.windows():
            for child in app_window.descendants():
                if str(child.window_text()).startswith(start_text):
                    return child
        return None

    @staticmethod
    def find_child_element_full(app: Application, start_text: str):
        """以开头字符串匹配窗口"""
        for app_window in app.windows():
            if app_window.window_text() == start_text:
                return app_window
            for child in app_window.descendants():
                if child.window_text() == start_text:
                    return child
        return None

    @staticmethod
    def find_child_element(window, child_name: str):
        """查找子元素"""
        for child in window.descendants():
            if child.window_text() == child_name:
                return child
        raise Exception("元素：%s 找不到" % child_name)
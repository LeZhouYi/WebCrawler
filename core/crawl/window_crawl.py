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
        assert os.path.exists(self.download_dir)

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
    def find_windows(name_pattern: str):
        """等待窗口出现并返回"""
        desktop = Desktop(backend="uia")
        windows = desktop.windows()
        # 遍历所有窗口，打印窗口标题和句柄
        match_windows = []
        for window in windows:
            if re.match(name_pattern, window.window_text()):
                match_windows.append(window)
        return match_windows

    @staticmethod
    def wait_window(name_pattern: str, children_title: str, wait_time: int = 30):
        """等待窗口出现并返回"""
        for i in range(wait_time):
            desktop = Desktop(backend="uia")
            windows = desktop.windows()
            # 遍历所有窗口，打印窗口标题和句柄
            for window in windows:
                if re.match(name_pattern, window.window_text()):
                    app = Application(backend="uia").connect(handle=window.handle)
                    main_window = app.windows()[0]
                    if len(main_window.children(title=children_title)) > 0:
                        return app
            time.sleep(1)
        raise Exception("等待窗口名称匹配：%s 并且子元素包含标题：%s 的窗口不存在" % (name_pattern, children_title))

    @staticmethod
    def wait_window_default(name_pattern: str, wait_time: int = 30):
        """等待窗口出现并返回"""
        for i in range(wait_time):
            desktop = Desktop(backend="uia")
            windows = desktop.windows()
            # 遍历所有窗口，打印窗口标题和句柄
            for window in windows:
                if re.match(name_pattern, window.window_text()):
                    app = Application(backend="uia").connect(handle=window.handle)
                    return app
            time.sleep(1)
        raise Exception("等待窗口名称匹配：%s 的窗口不存在" % name_pattern)

    @staticmethod
    def find_child_window(window, title_pattern):
        """通过标题查找子元素"""
        for children in window.children():
            if re.match(title_pattern, children.window_text()):
                return children
        raise Exception("查找子元素名称匹配：%s 时找不到" % title_pattern)

    @staticmethod
    def find_child_element(wrapper, title_pattern):
        """通过标题查找子元素"""
        for children in wrapper.descendants():
            if re.match(title_pattern, children.window_text()):
                return children
        raise Exception("查找子元素名称匹配：%s 时找不到" % title_pattern)

    @staticmethod
    def find_child_elements(wrapper, title_pattern):
        """通过标题查找子元素"""
        elements = []
        for children in wrapper.descendants():
            if re.match(title_pattern, children.window_text()):
                elements.append(children)
        return elements

    @staticmethod
    def wait_child_element(wrapper, title_pattern, wait_time: int = 30):
        for i in range(wait_time):
            for children in wrapper.descendants():
                if re.match(title_pattern, children.window_text()):
                    return children
            time.sleep(1)
        raise Exception("查找子元素名称匹配：%s 时找不到" % title_pattern)

    @staticmethod
    def wait_child_window(window, title_pattern, wait_time: int = 30):
        """等待子元素窗口"""
        for i in range(wait_time):
            for children in window.children():
                if re.match(title_pattern, children.window_text()):
                    return children
            time.sleep(1)
        raise Exception("等待子元素名称匹配：%s 时找不到" % title_pattern)

    @staticmethod
    def wait_child_window_disappear(window, title_pattern, wait_time: int = 30):
        """等待子元素消失"""
        for i in range(wait_time):
            is_disappear = True
            for children in window.children():
                if re.match(title_pattern, children.window_text()):
                    is_disappear = False
                    break
            if is_disappear:
                return
            time.sleep(1)
        raise Exception("等待子元素名称匹配：%s 消失时，等待%s秒后仍存在" % (title_pattern, wait_time))

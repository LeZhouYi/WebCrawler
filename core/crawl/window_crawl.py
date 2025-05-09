import os
import re
import threading
import time
from os import PathLike
from typing import Union, Optional, Sequence

import cv2
import numpy as np
from PIL import ImageGrab
from pywinauto import Desktop, Application
from pywinauto.controls.uia_controls import EditWrapper
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.keyboard import send_keys
from pywinauto.mouse import click

from core.config.config import get_config_by_section


class WindowCrawler:

    def __init__(self):
        self.download_dir = None  # 下载文件夹
        self.will_save_photo = get_config_by_section("crawl", "save_screenshot") == "True"
        self.init_window_crawler()

    def init_window_crawler(self):
        self.download_dir = os.path.join(os.getcwd(), get_config_by_section("crawl", "download_dir"))
        os.makedirs(self.download_dir, exist_ok=True)

    @staticmethod
    def start_app(filepath: Union[os.PathLike, str]):
        """启动APP"""
        threading.Thread(target=os.startfile, args=(filepath,)).start()

    def close_app_by_name(self, name_pattern: str):
        """通过APP名称关闭应用"""
        app = self.find_app_by_name(name_pattern)
        while app:
            app.kill()
            time.sleep(2)
            app = self.find_app_by_name(name_pattern)

    @staticmethod
    def find_app_by_name(name_pattern: str) -> Optional[Application]:
        """通过APP名称查找应用"""
        # 遍历所有窗口，打印窗口标题和句柄
        for window in Desktop(backend="uia").windows():
            if re.search(name_pattern, window.window_text()):
                app = Application(backend="uia").connect(handle=window.handle)
                return app

    def wait_app_by_name(self, name_pattern: str, times: int = 6, interval: int = 5):
        """等待APP名称对应的应用"""
        for _ in range(times):
            app = self.find_app_by_name(name_pattern)
            if app:
                return app
            time.sleep(interval)
        raise Exception("查找名称为：%s 的应用时找不到" % name_pattern)

    @staticmethod
    def find_window_by_name(app: Application, name_pattern: str, class_type: any = None):
        """通过名称和类型查找子窗口"""
        for window in app.windows():
            if re.search(name_pattern, window.window_text()):
                if class_type is None:
                    return window
                elif isinstance(window, class_type):
                    return window

    def wait_window_by_name(self, app: Application, name_pattern: str, class_type: any = None, times: int = 6,
                            interval: int = 5):
        """通过名称和类型查找子窗口"""
        for i in range(times):
            window = self.find_window_by_name(app, name_pattern, class_type)
            if window:
                return window
            time.sleep(interval)
        raise Exception("查找名称为：%s 的窗口时找不到" % name_pattern)

    @staticmethod
    def find_element_by_app(app: Application, name_pattern: str, class_type: any = None):
        """通过名称和类型查找子元素"""
        for window in app.windows():
            for child in window.descendants():
                if re.search(name_pattern, child.window_text()):
                    if class_type is None:
                        print(type(child))
                        return child
                    elif isinstance(child, class_type):
                        return child

    def wait_element_by_app(self, app: Application, name_pattern: str, class_type: any = None, times: int = 6,
                            interval: int = 5) -> UIAWrapper:
        """通过名称和类型查找子元素"""
        for i in range(times):
            element = self.find_element_by_app(app, name_pattern, class_type)
            if element:
                return element
            time.sleep(interval)
        raise Exception("查找名称为：%s 的元素时找不到" % name_pattern)

    @staticmethod
    def find_element_by_wrapper(wrapper: UIAWrapper, name_pattern: str, class_type: any = None) -> Optional[UIAWrapper]:
        """通过名称和类型查找子元素"""
        for child in wrapper.descendants():
            if re.search(name_pattern, child.window_text()):
                if class_type is None:
                    print(type(child))
                    return child
                elif isinstance(child, class_type):
                    return child

    def wait_element_by_wrapper(self, wrapper: UIAWrapper, name_pattern: str, class_type: any = None, times: int = 6,
                                interval: int = 5):
        """通过名称和类型查找子元素"""
        for i in range(times):
            element = self.find_element_by_wrapper(wrapper, name_pattern, class_type)
            if element:
                return element
            time.sleep(interval)
        raise Exception("查找名称为：%s 的元素时找不到" % name_pattern)

    @staticmethod
    def send_input_keys(input_element: EditWrapper, keys: str):
        """对元素进行输入操作"""
        input_element.set_focus()
        send_keys(keys)

    def save_screenshot(self, element: Union[Application, UIAWrapper], out_path: Union[os.PathLike, str],
                        filename: str = None) -> Union[PathLike, str, None]:
        """
            保存元素所属窗口的截图，MenuItemWrapper的父窗口可能没有，会报错
            pip install Pillow
        """
        try:
            if not self.will_save_photo:
                return None
            if not os.path.exists(out_path):
                os.makedirs(out_path, exist_ok=True)
            if filename is None:
                filename = "%s.png" % (int(time.time()))
                time.sleep(1)
            if isinstance(element, Application):
                parent = element.windows()[0]
            elif element.is_dialog():
                parent = element
            else:
                parent = element.parent()
                while parent and not parent.is_dialog():  # 判断是否为窗口层级
                    parent = parent.parent()
            filepath = os.path.join(out_path, filename)
            parent.capture_as_image().save(filepath)
            return filepath
        except Exception as e:
            raise Exception("截图失败：%s" % e)

    @staticmethod
    def find_element_by_id(app: Application, automation_id: str):
        """通过名称和类型查找子元素"""
        for window in app.windows():
            for child in window.descendants():
                if automation_id == str(child.automation_id()):
                    return child

    def wait_element_by_id(self, app: Application, automation_id: str, times: int = 6,
                           interval: int = 5):
        """通过名称和类型查找子元素"""
        for i in range(times):
            element = self.find_element_by_id(app, automation_id)
            if element:
                return element
            time.sleep(interval)
        raise Exception("查找automation_id为：%s 的元素时找不到" % automation_id)

    @staticmethod
    def get_parent_window(element: UIAWrapper):
        """获取父级窗口"""
        parent = element.parent()
        while parent and not parent.is_dialog():  # 判断是否为窗口层级
            parent = parent.parent()
        if parent is None:
            raise Exception("该元素上层没有窗口")
        return parent

    @staticmethod
    def click_by_template(window: UIAWrapper, template_path: Union[os.PathLike, str], relative_x: float = 0.5,
                          relative_y: float = 0.5, match_val: float = 0.8):
        """图片模板匹配点击"""
        rect = window.rectangle()
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

        screen = window.capture_as_image()
        screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

        # 模板匹配
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val < match_val:
            raise Exception("未找到匹配控件：%s" % template_path)

        # 计算坐标
        template_h, template_w = template.shape[:2]
        top_left_x, top_left_y = max_loc
        x = int(left + top_left_x + template_w * relative_x)
        y = int(top + top_left_y + template_h * relative_y)

        # 点击
        click(coords=(x, y))

    @staticmethod
    def find_by_template(window: UIAWrapper, template_path: Union[os.PathLike, str], match_val: float = 0.8
                         ) -> Optional[Sequence[int]]:
        """图片模板匹配元素"""
        screen = window.capture_as_image()
        screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

        # 模板匹配
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val < match_val:
            return None
        return max_loc

    def wait_by_template(self, window: UIAWrapper, template_path: Union[os.PathLike, str], match_val: float = 0.8,
                         times: int = 6, interval: int = 5):
        """图片模板匹配元素"""
        for i in range(times):
            max_loc = self.find_by_template(window, template_path, match_val)
            if max_loc:
                return max_loc
            time.sleep(interval)
        raise Exception("查找template_path为：%s 的元素时找不到" % template_path)

    @staticmethod
    def click_by_element(element: UIAWrapper, relative_x: float = 0.5, relative_y: float = 0.5):
        """根据元素位置点击"""
        rect = element.rectangle()
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        width = right - left
        height = bottom - top
        x = int(left + width * relative_x)
        y = int(top + height * relative_y)
        click(coords=(x, y))

    @staticmethod
    def input_keys(text: str, sleep_time: float = 0.5):
        send_keys(text)
        time.sleep(sleep_time)

    def save_desktop_shot(self, out_path: Union[os.PathLike, str], filename: str = None):
        """
            保存元素所属窗口的截图，MenuItemWrapper的父窗口可能没有，会报错
            pip install Pillow
        """
        try:
            if not self.will_save_photo:
                return
            if not os.path.exists(out_path):
                os.makedirs(out_path, exist_ok=True)
            if filename is None:
                filename = "%s.png" % (int(time.time()))
                time.sleep(1)
            ImageGrab.grab().save(os.path.join(out_path, filename))
        except Exception as e:
            raise Exception("截图失败：%s" % e)

    @staticmethod
    def find_elements_by_app(app: Application, name_pattern: str, class_type: any = None) -> list:
        """通过名称和类型查找所有匹配子元素"""
        children = []
        for window in app.windows():
            for child in window.descendants():
                if re.search(name_pattern, child.window_text()):
                    if class_type is None:
                        children.append(child)
                        break
                    elif isinstance(child, class_type):
                        children.append(child)
                        break
        return children

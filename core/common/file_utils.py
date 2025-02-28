import json
import os
from os import PathLike
from typing import Optional, Generator, Any, Union

import requests


def load_json_data(file_path: str) -> Optional[dict]:
    """
    读取Json数据
    :param file_path: 文件相对路径
    :return Json数据
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)


def get_stream_io(file_path: str, chunk_size: int = 1024) -> Generator[bytes, Any, None]:
    """获取文件流式传输流"""
    with open(file_path, "rb") as file:
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            yield data


def get_file_ext(filename: str) -> str:
    """
    获取文件名后缀
    :param filename:
    :return:
    """
    if filename.find(".") > -1:
        return filename.rsplit(".", 1)[1]
    return ""

def download_file(url: str, file_path: Union[PathLike, str, bytes]) -> bool:
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

def delete_file(filepath: Union[PathLike, str, bytes]) -> bool:
    """删除本地文件"""
    try:
        os.remove(filepath)
        return True
    except OSError:
        return False
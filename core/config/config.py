import json

with open("config/config.json", "r", encoding="utf-8") as file:
    __config = json.load(file)


def get_config(option: str):
    """
    读取当前配置对应字段的值
    :param option: [str]字段
    :return: [any]DEFAULT中字段对应的值
    """
    if option in __config:
        return __config[option]
    raise KeyError(option)


def get_config_by_section(section: str, option: str):
    """
    读取当前配置对应字段的值
    :param section: [str]对应节点
    :param option: [str]字段
    :return: [any]DEFAULT中字段对应的值
    """
    if section in __config:
        section_value = __config[section]
        if option in section_value:
            return section_value[option]
    raise KeyError(option)
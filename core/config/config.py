import configparser

__config = configparser.ConfigParser()
__config.read("config/config.ini", encoding="utf-8")


def get_config(option: str):
    """
    读取当前配置对应字段的值
    :param option: [str]字段
    :return: [any]DEFAULT中字段对应的值
    """
    return __config.get(section="DEFAULT", option=option)


def get_config_by_section(section: str, option: str):
    """
    读取当前配置对应字段的值
    :param section: [str]对应节点
    :param option: [str]字段
    :return: [any]DEFAULT中字段对应的值
    """
    return __config.get(section=section, option=option)

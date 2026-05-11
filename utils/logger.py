# utils/logger.py

DEBUG = False #默认不启用debug模式， Debug = True代表开启调试模式


def set_debug_mode(enabled: bool) -> None:
    """
    设置是否启用 debug 模式。

    enabled=True:
        显示完整调试信息，例如 JSON、Mermaid 代码、LLM 原始返回。
    enabled=False:
        只显示用户关心的简洁信息。
    """

    global DEBUG
    DEBUG = enabled  #把 Debug开关设置为用户传进来的值： True or Flase


def is_debug_mode() -> bool:
    """
    返回当前是否为 debug 模式。
    """

    return DEBUG


def log_info(message: str) -> None:
    """
    普通信息，无论 normal / debug 都显示。
    """

    print(message)


def log_debug(message: str) -> None:
    """
    调试信息，只在 debug 模式下显示。
    """

    if DEBUG:
        print(message)


def log_section(title: str) -> None:
    """
    打印阶段标题。
    """

    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)
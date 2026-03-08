"""
工具函数模块

[原创选型]
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    设置日志 [原创选型]

    Args:
        level: 日志级别

    Returns:
        Logger: 配置好的日志器
    """
    logger = logging.getLogger("chaos_code")

    # 避免重复配置
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 控制台处理器
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    # 格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从当前目录向上查找，直到找到 .git 或 pyproject.toml
    current = Path.cwd()

    while current != current.parent:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent

    return Path.cwd()

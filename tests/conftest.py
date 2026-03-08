"""
Pytest 配置文件
"""

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录 fixture"""
    return tmp_path

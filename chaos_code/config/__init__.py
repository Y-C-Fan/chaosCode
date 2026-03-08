"""
配置系统模块

[原创选型: pydantic-settings]
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置 [原创选型]

    支持从环境变量和 .env 文件加载配置
    """

    model_config = SettingsConfigDict(
        env_prefix="CHAOS_CODE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 配置
    default_model: str = Field(default="gpt-4o", description="默认模型")
    api_key: Optional[str] = Field(default=None, description="API Key")
    api_base: Optional[str] = Field(default=None, description="API Base URL")

    # Agent 配置
    max_turns: int = Field(default=20, description="最大对话轮数")
    default_mode: str = Field(default="build", description="默认模式")

    # 工具配置
    max_output_length: int = Field(default=10000, description="工具输出最大长度")
    command_timeout: int = Field(default=120000, description="命令超时（毫秒）")

    # 调试配置
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")


# 全局配置实例
settings = Settings()

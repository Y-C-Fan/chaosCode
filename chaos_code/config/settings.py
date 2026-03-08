"""
配置系统模块

[原创选型: pydantic-settings]
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPServerConfigModel(BaseSettings):
    """MCP 服务器配置模型"""

    name: str = Field(..., description="服务器名称")
    command: str = Field(..., description="启动命令")
    args: List[str] = Field(default_factory=list, description="命令参数")
    env: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    cwd: Optional[str] = Field(default=None, description="工作目录")
    disabled: bool = Field(default=False, description="是否禁用")


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

    # 权限配置
    permission_default_level: str = Field(
        default="confirm",
        description="默认权限级别: allow/deny/confirm",
    )
    permission_confirm_timeout: int = Field(default=60, description="权限确认超时（秒）")
    permission_config_path: Optional[str] = Field(
        default=None,
        description="权限配置文件路径",
    )
    auto_confirm: bool = Field(
        default=False,
        description="自动确认所有操作（危险，仅用于测试）",
    )

    # MCP 配置
    mcp_config_path: Optional[str] = Field(
        default=None,
        description="MCP 服务器配置文件路径",
    )
    mcp_servers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="MCP 服务器配置列表",
    )

    # 调试配置
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")

    @field_validator("mcp_servers", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v):
        """解析 MCP 服务器配置"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v

    def load_mcp_config(self) -> List[Dict[str, Any]]:
        """
        加载 MCP 服务器配置

        优先从 mcp_config_path 指定的文件加载，
        否则使用 mcp_servers 配置

        Returns:
            List[Dict[str, Any]]: MCP 服务器配置列表
        """
        # 如果指定了配置文件路径
        if self.mcp_config_path:
            config_path = Path(self.mcp_config_path)
            if config_path.exists():
                try:
                    content = config_path.read_text(encoding="utf-8")
                    if config_path.suffix == ".json":
                        data = json.loads(content)
                    elif config_path.suffix in (".yaml", ".yml"):
                        import yaml
                        data = yaml.safe_load(content)
                    else:
                        return self.mcp_servers

                    # 支持两种格式
                    if "mcpServers" in data:
                        servers = []
                        for name, config in data["mcpServers"].items():
                            config["name"] = name
                            servers.append(config)
                        return servers
                    elif isinstance(data, list):
                        return data
                    else:
                        return self.mcp_servers

                except Exception:
                    return self.mcp_servers

        return self.mcp_servers


# 全局配置实例
settings = Settings()

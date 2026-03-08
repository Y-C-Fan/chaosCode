"""
Write 工具 - 文件写入

[OpenCode 参考: write.ts 实现]
"""

import os
from typing import Any, Dict

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class WriteTool(ToolBase):
    """
    文件写入工具 [OpenCode 参考]

    创建新文件或覆盖现有文件
    """

    name = "write"
    description = "写入文件内容，会覆盖已存在的文件"

    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要写入的文件路径（绝对路径）",
            },
            "content": {
                "type": "string",
                "description": "要写入的内容",
            },
            "create_dirs": {
                "type": "boolean",
                "description": "是否自动创建父目录",
                "default": True,
            },
        },
        "required": ["file_path", "content"],
    }

    def should_confirm(self, params: Dict[str, Any]) -> bool:
        """检查是否需要确认 [Gemini CLI 参考]"""
        file_path = params.get("file_path", "")

        # 覆盖已存在的文件需要确认
        if os.path.exists(file_path):
            return True

        return False

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        action = "覆盖" if os.path.exists(file_path) else "创建"
        return f"{action}文件: {file_path} ({len(content)} 字符)"

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """写入文件"""
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        create_dirs = params.get("create_dirs", True)

        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        # 解析路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)

        try:
            # 创建父目录
            if create_dirs:
                parent_dir = os.path.dirname(file_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # 获取文件信息
            file_size = os.path.getsize(file_path)
            lines = content.count("\n") + 1 if content else 0

            return ToolResult(
                success=True,
                output=f"成功写入文件: {file_path}\n大小: {file_size} 字节\n行数: {lines}",
                metadata={"file_path": file_path, "size": file_size, "lines": lines},
            )

        except PermissionError:
            return ToolResult(success=False, error=f"没有权限写入文件: {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

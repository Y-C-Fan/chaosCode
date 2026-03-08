"""
Edit 工具 - 文件编辑

[OpenCode 参考: edit.ts 实现]
"""

import os
from typing import Any, Dict, List, Optional

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class EditTool(ToolBase):
    """
    文件编辑工具 [OpenCode 参考]

    使用字符串替换方式编辑文件，支持精确匹配
    """

    name = "edit"
    description = "编辑文件，使用字符串替换。可以指定 old_string 替换为 new_string"

    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要编辑的文件路径",
            },
            "old_string": {
                "type": "string",
                "description": "要被替换的原始字符串（必须精确匹配）",
            },
            "new_string": {
                "type": "string",
                "description": "替换后的新字符串",
            },
            "replace_all": {
                "type": "boolean",
                "description": "是否替换所有匹配项",
                "default": False,
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def should_confirm(self, params: Dict[str, Any]) -> bool:
        """检查是否需要确认"""
        # 编辑操作总是需要确认
        return True

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        file_path = params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        replace_all = params.get("replace_all", False)

        old_preview = old_string[:30] + "..." if len(old_string) > 30 else old_string
        new_preview = new_string[:30] + "..." if len(new_string) > 30 else new_string

        action = "全部替换" if replace_all else "替换"
        return f"{action} {file_path}: '{old_preview}' -> '{new_preview}'"

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """编辑文件"""
        file_path = params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        replace_all = params.get("replace_all", False)

        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        if not old_string:
            return ToolResult(success=False, error="old_string 不能为空")

        # 解析路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return ToolResult(success=False, error=f"文件不存在: {file_path}")

        if os.path.isdir(file_path):
            return ToolResult(success=False, error=f"路径是目录，不是文件: {file_path}")

        try:
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查 old_string 是否存在
            if old_string not in content:
                return ToolResult(
                    success=False,
                    error=f"未找到要替换的字符串。请确保 old_string 精确匹配文件中的内容。",
                )

            # 计算替换次数
            if replace_all:
                count = content.count(old_string)
            else:
                count = 1
                # 检查是否有多个匹配
                if content.count(old_string) > 1:
                    return ToolResult(
                        success=False,
                        error=f"找到 {content.count(old_string)} 处匹配。请使用更具体的 old_string 或设置 replace_all=True",
                    )

            # 执行替换
            if replace_all:
                new_content = content.replace(old_string, new_string)
            else:
                new_content = content.replace(old_string, new_string, 1)

            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                success=True,
                output=f"成功编辑文件: {file_path}\n替换次数: {count}",
                metadata={"file_path": file_path, "replacements": count},
            )

        except PermissionError:
            return ToolResult(success=False, error=f"没有权限编辑文件: {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

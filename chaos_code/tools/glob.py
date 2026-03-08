"""
Glob 工具 - 文件模式匹配

[OpenCode 参考: glob.ts 实现]
"""

import os
from fnmatch import fnmatch
from typing import Any, Dict, List

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class GlobTool(ToolBase):
    """
    文件模式匹配工具 [OpenCode 参考]

    使用 glob 模式搜索文件，支持 ** 和 * 通配符
    """

    name = "glob"
    description = "使用 glob 模式搜索文件，支持 ** 递归匹配和 * 单层匹配"

    parameters_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "glob 模式，如 '**/*.py' 或 'src/**/*.ts'",
            },
            "path": {
                "type": "string",
                "description": "搜索起始目录，默认当前目录",
            },
            "exclude": {
                "type": "array",
                "items": {"type": "string"},
                "description": "排除的模式列表",
            },
        },
        "required": ["pattern"],
    }

    # 默认排除的目录
    DEFAULT_EXCLUDES = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".tox",
        ".eggs",
        "*.egg-info",
        "dist",
        "build",
        ".mypy_cache",
        ".ruff_cache",
    ]

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """执行 glob 搜索"""
        pattern = params.get("pattern", "")
        path = params.get("path", context.working_directory)
        exclude = params.get("exclude", [])

        if not pattern:
            return ToolResult(success=False, error="搜索模式不能为空")

        # 解析路径
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)

        if not os.path.exists(path):
            return ToolResult(success=False, error=f"目录不存在: {path}")

        # 合并排除列表
        excludes = self.DEFAULT_EXCLUDES + exclude

        try:
            # 执行搜索
            matches = self._glob_search(path, pattern, excludes)

            if not matches:
                return ToolResult(
                    success=True,
                    output=f"未找到匹配 '{pattern}' 的文件",
                    metadata={"count": 0},
                )

            # 排序（按修改时间降序）
            matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            # 格式化输出
            output_lines = [f"找到 {len(matches)} 个匹配 '{pattern}' 的文件:\n"]
            for match in matches:
                # 显示相对路径
                rel_path = os.path.relpath(match, path)
                output_lines.append(f"  {rel_path}")

            output = "\n".join(output_lines)
            output = self._truncate_output(output, context.max_output_length)

            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(matches), "files": matches[:100]},  # 限制返回数量
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _glob_search(
        self,
        base_path: str,
        pattern: str,
        excludes: List[str],
    ) -> List[str]:
        """
        执行 glob 搜索

        Args:
            base_path: 基础路径
            pattern: glob 模式
            excludes: 排除模式列表

        Returns:
            匹配的文件路径列表
        """
        matches = []

        # 规范化模式
        if not pattern.startswith("/"):
            pattern = os.path.join(base_path, pattern)

        # 将 glob 模式转换为正则匹配
        for root, dirs, files in os.walk(base_path):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if not self._should_exclude(d, excludes)]

            # 检查文件
            for filename in files:
                file_path = os.path.join(root, filename)

                # 检查是否匹配模式
                if self._match_pattern(file_path, pattern):
                    matches.append(file_path)

        return matches

    def _should_exclude(self, name: str, excludes: List[str]) -> bool:
        """检查是否应该排除"""
        for exclude in excludes:
            if fnmatch(name, exclude):
                return True
        return False

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        匹配 glob 模式

        支持:
            * 匹配任意字符（不含路径分隔符）
            ** 匹配任意字符（含路径分隔符）
            ? 匹配单个字符
        """
        # 简单实现：使用 fnmatch
        # AIDEV-NOTE: 后续可以实现更完整的 glob 匹配
        import fnmatch

        # 规范化路径
        norm_path = os.path.normpath(path)
        norm_pattern = os.path.normpath(pattern)

        # 处理 ** 模式
        if "**" in norm_pattern:
            # 转换为正则表达式
            import re

            regex_pattern = norm_pattern.replace("**", ".*").replace("*", "[^/]*").replace("?", ".")
            regex_pattern = f"^{regex_pattern}$"
            return bool(re.match(regex_pattern, norm_path))

        return fnmatch.fnmatch(norm_path, norm_pattern)

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        return f"搜索文件: {pattern} (在 {path})"

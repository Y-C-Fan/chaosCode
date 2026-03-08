"""
Grep 工具 - 内容搜索

[OpenCode 参考: grep.ts 实现]
"""

import os
import re
from typing import Any, Dict, List, Optional

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class GrepTool(ToolBase):
    """
    内容搜索工具 [OpenCode 参考]

    使用正则表达式搜索文件内容
    """

    name = "grep"
    description = "在文件中搜索匹配正则表达式的内容"

    parameters_schema = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "正则表达式模式",
            },
            "path": {
                "type": "string",
                "description": "搜索路径，默认当前目录",
            },
            "glob": {
                "type": "string",
                "description": "文件过滤模式，如 '*.py'",
            },
            "type": {
                "type": "string",
                "description": "文件类型过滤，如 'py', 'js', 'ts'",
            },
            "output_mode": {
                "type": "string",
                "enum": ["content", "files_with_matches", "count"],
                "description": "输出模式: content(显示内容), files_with_matches(仅文件名), count(计数)",
                "default": "content",
            },
            "-i": {
                "type": "boolean",
                "description": "忽略大小写",
                "default": False,
            },
            "head_limit": {
                "type": "number",
                "description": "限制输出数量",
            },
            "context": {
                "type": "number",
                "description": "显示匹配行的上下文行数",
            },
        },
        "required": ["pattern"],
    }

    # 文件类型到扩展名的映射
    TYPE_EXTENSIONS = {
        "py": [".py"],
        "js": [".js", ".jsx", ".mjs"],
        "ts": [".ts", ".tsx"],
        "go": [".go"],
        "java": [".java"],
        "rust": [".rs"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
        "rb": [".rb"],
        "php": [".php"],
        "md": [".md"],
        "json": [".json"],
        "yaml": [".yaml", ".yml"],
        "html": [".html", ".htm"],
        "css": [".css", ".scss", ".sass"],
        "sh": [".sh", ".bash", ".zsh"],
    }

    # 排除的目录
    EXCLUDE_DIRS = {
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
    }

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """执行内容搜索"""
        pattern = params.get("pattern", "")
        path = params.get("path", context.working_directory)
        glob_pattern = params.get("glob")
        file_type = params.get("type")
        output_mode = params.get("output_mode", "content")
        ignore_case = params.get("-i", False)
        head_limit = params.get("head_limit")
        context_lines = params.get("context", 0)

        if not pattern:
            return ToolResult(success=False, error="搜索模式不能为空")

        # 解析路径
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)

        if not os.path.exists(path):
            return ToolResult(success=False, error=f"路径不存在: {path}")

        try:
            # 编译正则表达式
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, flags)

            # 获取文件扩展名过滤
            extensions = None
            if file_type and file_type in self.TYPE_EXTENSIONS:
                extensions = set(self.TYPE_EXTENSIONS[file_type])

            # 执行搜索
            results = self._search(
                path=path,
                regex=regex,
                glob_pattern=glob_pattern,
                extensions=extensions,
                output_mode=output_mode,
                head_limit=head_limit,
                context_lines=context_lines,
            )

            if not results:
                return ToolResult(
                    success=True,
                    output=f"未找到匹配 '{pattern}' 的内容",
                    metadata={"count": 0},
                )

            # 格式化输出
            output = self._format_results(results, output_mode)
            output = self._truncate_output(output, context.max_output_length)

            return ToolResult(
                success=True,
                output=output,
                metadata={"count": len(results)},
            )

        except re.error as e:
            return ToolResult(success=False, error=f"无效的正则表达式: {e}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _search(
        self,
        path: str,
        regex: re.Pattern,
        glob_pattern: Optional[str],
        extensions: Optional[set],
        output_mode: str,
        head_limit: Optional[int],
        context_lines: int,
    ) -> List[Dict[str, Any]]:
        """执行搜索"""
        results = []
        count = 0

        # 确定是文件还是目录
        if os.path.isfile(path):
            files = [path]
        else:
            files = self._get_files(path, glob_pattern, extensions)

        for file_path in files:
            if head_limit and count >= head_limit:
                break

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                file_results = []
                for i, line in enumerate(lines):
                    if regex.search(line):
                        file_results.append(
                            {
                                "file": file_path,
                                "line": i + 1,
                                "content": line.rstrip("\n"),
                                "context": self._get_context(lines, i, context_lines),
                            }
                        )
                        count += 1

                if file_results:
                    if output_mode == "files_with_matches":
                        results.append({"file": file_path})
                    elif output_mode == "count":
                        results.append({"file": file_path, "count": len(file_results)})
                    else:
                        results.extend(file_results)

            except (IOError, OSError):
                continue

        return results

    def _get_files(
        self,
        path: str,
        glob_pattern: Optional[str],
        extensions: Optional[set],
    ) -> List[str]:
        """获取要搜索的文件列表"""
        files = []

        for root, dirs, filenames in os.walk(path):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]

            for filename in filenames:
                file_path = os.path.join(root, filename)

                # 检查扩展名
                if extensions:
                    ext = os.path.splitext(filename)[1]
                    if ext not in extensions:
                        continue

                # 检查 glob 模式
                if glob_pattern:
                    from fnmatch import fnmatch

                    if not fnmatch(filename, glob_pattern):
                        continue

                files.append(file_path)

        return files

    def _get_context(
        self,
        lines: List[str],
        index: int,
        context_lines: int,
    ) -> Dict[str, List[str]]:
        """获取上下文行"""
        if context_lines <= 0:
            return {}

        start = max(0, index - context_lines)
        end = min(len(lines), index + context_lines + 1)

        return {
            "before": [lines[i].rstrip("\n") for i in range(start, index)],
            "after": [lines[i].rstrip("\n") for i in range(index + 1, end)],
        }

    def _format_results(
        self,
        results: List[Dict[str, Any]],
        output_mode: str,
    ) -> str:
        """格式化输出结果"""
        lines = []

        if output_mode == "files_with_matches":
            for r in results:
                lines.append(r["file"])
        elif output_mode == "count":
            for r in results:
                lines.append(f"{r['count']:6}\t{r['file']}")
        else:
            current_file = None
            for r in results:
                if r["file"] != current_file:
                    current_file = r["file"]
                    lines.append(f"\n{current_file}:")

                # 添加上下文
                context = r.get("context", {})
                if context.get("before"):
                    for ctx_line in context["before"]:
                        lines.append(f"  {r['line'] - len(context['before'])}\t{ctx_line}")

                lines.append(f"{r['line']:6}\t{r['content']}")

                if context.get("after"):
                    for ctx_line in context["after"]:
                        lines.append(f"  {r['line'] + 1}\t{ctx_line}")

        return "\n".join(lines)

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        return f"搜索内容: '{pattern}' (在 {path})"

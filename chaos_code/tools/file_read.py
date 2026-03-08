"""
Read 工具 - 文件读取

[OpenCode 参考: read.ts 实现]
"""

import os
from typing import Any, Dict, List, Optional

from chaos_code.tools.base import ToolBase, ToolContext, ToolResult


class ReadTool(ToolBase):
    """
    文件读取工具 [OpenCode 参考]

    支持读取文件、指定行范围、读取图片等
    """

    name = "read"
    description = "读取文件内容，支持文本文件和图片文件"

    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "要读取的文件路径（绝对路径或相对路径）",
            },
            "offset": {
                "type": "number",
                "description": "起始行号（从 1 开始），默认从文件开头读取",
            },
            "limit": {
                "type": "number",
                "description": "读取的最大行数，默认读取整个文件",
            },
            "pages": {
                "type": "string",
                "description": "PDF 文件的页码范围，如 '1-5' 或 '1,3,5'",
            },
        },
        "required": ["file_path"],
    }

    # 支持的图片格式
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}

    # 支持的文档格式
    DOC_EXTENSIONS = {".pdf", ".docx", ".doc"}

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """读取文件内容"""
        file_path = params.get("file_path", "")
        offset = params.get("offset", 1)
        limit = params.get("limit")
        pages = params.get("pages")

        if not file_path:
            return ToolResult(success=False, error="文件路径不能为空")

        # 解析路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return ToolResult(success=False, error=f"文件不存在: {file_path}")

        if os.path.isdir(file_path):
            return ToolResult(success=False, error=f"路径是目录，不是文件: {file_path}")

        # 获取文件扩展名
        ext = os.path.splitext(file_path)[1].lower()

        try:
            # 处理图片文件
            if ext in self.IMAGE_EXTENSIONS:
                return self._read_image(file_path, context)

            # 处理 PDF 文件
            if ext == ".pdf" and pages:
                return self._read_pdf_pages(file_path, pages, context)

            # 处理普通文本文件
            return self._read_text_file(file_path, offset, limit, context)

        except PermissionError:
            return ToolResult(success=False, error=f"没有权限读取文件: {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _read_text_file(
        self,
        file_path: str,
        offset: int,
        limit: Optional[int],
        context: ToolContext,
    ) -> ToolResult:
        """读取文本文件"""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        start = max(1, offset) - 1  # 转为 0-indexed
        end = len(lines) if limit is None else start + limit

        selected_lines = lines[start:end]

        # 格式化输出（带行号）
        output_lines = []
        for i, line in enumerate(selected_lines, start=start + 1):
            # 去除行尾换行符
            line_content = line.rstrip("\n")
            output_lines.append(f"{i:6}\t{line_content}")

        output = "\n".join(output_lines)

        # 添加文件信息
        info = f"文件: {file_path}\n总行数: {total_lines}\n显示: {start + 1}-{min(end, total_lines)}\n"

        return ToolResult(
            success=True,
            output=info + output,
            metadata={
                "total_lines": total_lines,
                "start_line": start + 1,
                "end_line": min(end, total_lines),
            },
        )

    def _read_image(self, file_path: str, context: ToolContext) -> ToolResult:
        """读取图片文件"""
        # AIDEV-NOTE: 图片读取需要后续实现 base64 编码或多模态处理
        # 目前返回基本信息
        file_size = os.path.getsize(file_path)
        return ToolResult(
            success=True,
            output=f"[图片文件: {file_path}]\n大小: {file_size} 字节\n（图片预览功能待实现）",
            metadata={"type": "image", "size": file_size},
        )

    def _read_pdf_pages(
        self,
        file_path: str,
        pages: str,
        context: ToolContext,
    ) -> ToolResult:
        """读取 PDF 指定页面"""
        # AIDEV-NOTE: PDF 读取需要额外依赖，后续实现
        return ToolResult(
            success=False,
            error="PDF 读取功能待实现，需要安装 PyPDF2 或 pdfplumber",
        )

    def get_description(self, params: Dict[str, Any]) -> str:
        """获取执行描述"""
        file_path = params.get("file_path", "")
        offset = params.get("offset")
        limit = params.get("limit")

        desc = f"读取文件: {file_path}"
        if offset or limit:
            desc += f" (行 {offset or 1}"
            if limit:
                desc += f"-{(offset or 1) + limit - 1}"
            desc += ")"
        return desc

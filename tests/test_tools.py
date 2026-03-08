"""
工具模块测试
"""

import os
import tempfile

import pytest

from chaos_code.tools import (
    BashTool,
    EditTool,
    GlobTool,
    GrepTool,
    ReadTool,
    ToolRegistry,
    WriteTool,
    default_tools,
)
from chaos_code.tools.base import ToolContext


def test_tool_registry():
    """测试工具注册表"""
    registry = ToolRegistry()

    tool = ReadTool()
    registry.register(tool)

    assert registry.has("read")
    assert registry.get("read") == tool
    assert "read" in registry.list_tools()


def test_default_tools():
    """测试默认工具集"""
    registry = default_tools()

    assert registry.has("bash")
    assert registry.has("read")
    assert registry.has("write")
    assert registry.has("edit")
    assert registry.has("glob")
    assert registry.has("grep")


def test_read_tool_schema():
    """测试 ReadTool Schema"""
    tool = ReadTool()
    schema = tool.get_schema()

    assert schema.name == "read"
    assert "file_path" in schema.parameters["properties"]


def test_bash_tool_dangerous_commands():
    """测试 BashTool 危险命令检测"""
    tool = BashTool()

    # 危险命令需要确认
    assert tool.should_confirm({"command": "rm -rf /"})
    assert tool.should_confirm({"command": "rm file.txt"})

    # 普通命令不需要确认
    assert not tool.should_confirm({"command": "ls -la"})
    assert not tool.should_confirm({"command": "echo hello"})


def test_write_tool_should_confirm():
    """测试 WriteTool 确认机制"""
    tool = WriteTool()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name

    try:
        # 覆盖已存在的文件需要确认
        assert tool.should_confirm({"file_path": temp_path})

        # 新文件不需要确认
        assert not tool.should_confirm({"file_path": "/nonexistent/path.txt"})
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_read_tool_execute():
    """测试 ReadTool 执行"""
    tool = ReadTool()
    context = ToolContext()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, ChaosCode!\n这是测试内容。")
        temp_path = f.name

    try:
        result = await tool.execute({"file_path": temp_path}, context)

        assert result.success
        assert "Hello, ChaosCode" in result.output
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_write_tool_execute():
    """测试 WriteTool 执行"""
    tool = WriteTool()
    context = ToolContext()

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "test.txt")
        content = "测试内容\n第二行"

        result = await tool.execute(
            {"file_path": file_path, "content": content},
            context,
        )

        assert result.success
        assert os.path.exists(file_path)

        with open(file_path) as f:
            assert f.read() == content


@pytest.mark.asyncio
async def test_edit_tool_execute():
    """测试 EditTool 执行"""
    tool = EditTool()
    context = ToolContext()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello World\nPython is great")
        temp_path = f.name

    try:
        result = await tool.execute(
            {
                "file_path": temp_path,
                "old_string": "World",
                "new_string": "ChaosCode",
            },
            context,
        )

        assert result.success

        with open(temp_path) as f:
            content = f.read()
            assert "ChaosCode" in content
            assert "World" not in content
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_glob_tool_execute():
    """测试 GlobTool 执行"""
    tool = GlobTool()
    context = ToolContext()

    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建一些测试文件
        for name in ["test1.py", "test2.py", "readme.md"]:
            open(os.path.join(temp_dir, name), "w").close()

        result = await tool.execute(
            {"pattern": "*.py", "path": temp_dir},
            context,
        )

        assert result.success
        assert result.metadata["count"] == 2


@pytest.mark.asyncio
async def test_grep_tool_execute():
    """测试 GrepTool 执行"""
    tool = GrepTool()
    context = ToolContext()

    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello')\n\ndef world():\n    print('World')")

        result = await tool.execute(
            {"pattern": "def", "path": temp_dir, "output_mode": "content"},
            context,
        )

        assert result.success
        assert result.metadata["count"] == 2

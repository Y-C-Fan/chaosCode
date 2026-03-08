"""
TUI 模块测试

[原创选型: textual TUI 框架]
"""

import pytest

from chaos_code.tui import (
    ChaosCodeApp,
    MessageList,
    InputArea,
    StatusBar,
    run_tui,
)


class TestChaosCodeApp:
    """测试 TUI 应用"""

    def test_app_creation(self):
        """测试应用创建"""
        app = ChaosCodeApp(model="gpt-4o", mode="build")

        assert app.model == "gpt-4o"
        assert app.mode == "build"

    def test_app_default_values(self):
        """测试默认值"""
        app = ChaosCodeApp()

        # 应该使用配置中的默认值
        assert app.model is not None
        assert app.mode is not None

    def test_app_bindings(self):
        """测试快捷键绑定"""
        app = ChaosCodeApp()

        # 检查绑定是否存在
        bindings = app.BINDINGS
        binding_keys = [b.key for b in bindings]

        assert "ctrl+q" in binding_keys  # 退出
        assert "ctrl+l" in binding_keys  # 清屏
        assert "ctrl+n" in binding_keys  # 新会话


class TestMessageList:
    """测试消息列表组件"""

    def test_message_list_creation(self):
        """测试消息列表创建"""
        message_list = MessageList()

        assert message_list is not None
        assert len(message_list._messages) == 0


class TestInputArea:
    """测试输入区域组件"""

    def test_input_area_creation(self):
        """测试输入区域创建"""
        input_area = InputArea()

        assert input_area is not None


class TestStatusBar:
    """测试状态栏组件"""

    def test_status_bar_creation(self):
        """测试状态栏创建"""
        status_bar = StatusBar(model="test-model", mode="build")

        assert status_bar.model == "test-model"
        assert status_bar.mode == "build"
        assert status_bar.status == "就绪"

    def test_status_bar_reactive(self):
        """测试状态栏响应式更新"""
        status_bar = StatusBar(model="model1", mode="build")

        # 更新属性
        status_bar.model = "model2"
        status_bar.status = "思考中..."

        assert status_bar.model == "model2"
        assert status_bar.status == "思考中..."


class TestRunTUI:
    """测试 TUI 启动函数"""

    def test_run_tui_function_exists(self):
        """测试启动函数存在"""
        assert callable(run_tui)

    def test_run_tui_creates_app(self):
        """测试启动函数创建应用"""
        # 不实际运行，只检查能创建应用实例
        import chaos_code.tui.app as tui_app

        # 保存原始 run 方法
        original_run = tui_app.ChaosCodeApp.run

        # 模拟 run 方法
        app_instance = None

        def mock_run(self):
            nonlocal app_instance
            app_instance = self

        tui_app.ChaosCodeApp.run = mock_run

        try:
            run_tui(model="test-model", mode="plan")
            assert app_instance is not None
            assert app_instance.model == "test-model"
            assert app_instance.mode == "plan"
        finally:
            # 恢复原始方法
            tui_app.ChaosCodeApp.run = original_run

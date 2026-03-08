"""
Agent 模块测试
"""

import pytest

from chaos_code.agent import AgentMode, CodingAgent, PlannerAgent
from chaos_code.llm import Message
from chaos_code.tools import ToolRegistry


class MockLLM:
    """Mock LLM for testing"""

    def __init__(self):
        self.model = "mock-model"

    async def generate(self, messages, tools=None, **kwargs):
        from chaos_code.llm import LLMResponse

        return LLMResponse(
            message=Message.assistant("这是模拟响应"),
            finish_reason="stop",
            model=self.model,
        )


def test_agent_mode():
    """测试 Agent 模式枚举"""
    assert AgentMode.BUILD.value == "build"
    assert AgentMode.PLAN.value == "plan"


def test_coding_agent_init():
    """测试 CodingAgent 初始化"""
    llm = MockLLM()
    tools = ToolRegistry()

    agent = CodingAgent(llm, tools)

    assert agent.mode == AgentMode.BUILD
    assert agent.max_turns == 20
    assert len(agent.messages) == 0


def test_planner_agent_init():
    """测试 PlannerAgent 初始化"""
    llm = MockLLM()
    tools = ToolRegistry()

    agent = PlannerAgent(llm, tools)

    assert agent.mode == AgentMode.PLAN
    assert agent.max_turns == 20


def test_agent_add_message():
    """测试添加消息"""
    llm = MockLLM()
    tools = ToolRegistry()
    agent = CodingAgent(llm, tools)

    agent.add_message(Message.user("测试消息"))

    assert len(agent.messages) == 1
    assert agent.messages[0].role == "user"


def test_agent_clear_history():
    """测试清除历史"""
    llm = MockLLM()
    tools = ToolRegistry()
    agent = CodingAgent(llm, tools)

    agent.add_message(Message.user("消息1"))
    agent.add_message(Message.assistant("消息2"))

    agent.clear_history()

    assert len(agent.messages) == 0

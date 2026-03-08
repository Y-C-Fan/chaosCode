"""
LLM 提供者实现

[MS-Agent 参考: 多后端实现]
"""

from typing import Optional

from chaos_code.llm.providers.litellm_provider import LiteLLMProvider

__all__ = ["LiteLLMProvider", "create_llm"]


def create_llm(
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> LiteLLMProvider:
    """
    创建 LLM 实例 [MS-Agent 参考]

    使用 litellm 作为统一后端，支持 OpenAI、Anthropic、DeepSeek 等

    Args:
        model: 模型名称，如 "gpt-4o", "claude-3-opus", "deepseek-chat"
        api_key: API 密钥
        base_url: API 基础 URL
        **kwargs: 额外配置

    Returns:
        LiteLLMProvider: LLM 实例

    Examples:
        >>> llm = create_llm("gpt-4o")
        >>> llm = create_llm("claude-3-opus", api_key="sk-...")
        >>> llm = create_llm("deepseek-chat", base_url="https://api.deepseek.com")
    """
    return LiteLLMProvider(model=model, api_key=api_key, base_url=base_url, **kwargs)

import json
from typing import Any, List, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

_MOCK_SEGMENTS: List[str] = [
    "议题一：产品定位与目标用户。张三提出 V2.0 版本应聚焦中小企业用户，"
    "降低使用门槛并优化核心功能流程，团队一致同意该方向。",
    "议题二：技术架构选型。李四建议采用微服务架构，将用户服务、订单服务"
    "与支付服务拆分，以支撑更高的并发与后续独立扩展。",
    "议题三：上线时间与里程碑。张三提议 Q3 完成内测、Q4 正式上线，"
    "李四确认开发周期约 6 周，赵六要求预留 2 周测试窗口。",
]

_MOCK_SUMMARY: str = (
    "本次会议围绕新产品 V2.0 开发规划展开，确认了三大核心议题："
    "一是产品定位聚焦中小企业用户；二是技术架构向微服务演进，"
    "拆分用户、订单、支付三大服务；三是明确 Q3 内测、Q4 上线的里程碑计划，"
    "并约定各负责人在 8 月完成原型、架构文档与测试计划。"
)

_MOCK_ACTION_ITEMS: List[dict] = [
    {"content": "完成产品原型设计", "owner": "张三", "deadline": "2025-08-15"},
    {"content": "输出技术架构文档", "owner": "李四", "deadline": "2025-08-20"},
    {"content": "制定 Q3 测试计划", "owner": "赵六", "deadline": "2025-08-30"},
]


class MockChatModel:
    """Offline stand-in for DeepSeek, returns preset payloads by prompt keyword."""

    def invoke(self, messages: Any, **kwargs: Any) -> AIMessage:
        text = self._extract_text(messages)
        # Use instruction-level keywords that won't appear in the transcript body
        if "extract_action_items" in text:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "extract_action_items",
                        "args": {"action_items": _MOCK_ACTION_ITEMS},
                        "id": "mock_call_1",
                    }
                ],
            )
        if "会议摘要" in text:
            return AIMessage(content=_MOCK_SUMMARY)
        if "按议题分割" in text:
            return AIMessage(content=json.dumps(_MOCK_SEGMENTS, ensure_ascii=False))
        return AIMessage(content="Mock LLM response.")

    def bind_tools(self, tools: Any, **kwargs: Any) -> "MockChatModel":
        return self

    @staticmethod
    def _extract_text(messages: Any) -> str:
        if isinstance(messages, str):
            return messages
        if isinstance(messages, BaseMessage):
            content = messages.content
            return content if isinstance(content, str) else str(content)
        if isinstance(messages, list):
            parts: List[str] = []
            for m in messages:
                if isinstance(m, BaseMessage):
                    c = m.content
                    parts.append(c if isinstance(c, str) else str(c))
                elif isinstance(m, str):
                    parts.append(m)
            return "\n".join(parts)
        return str(messages)


def get_llm() -> Union[BaseChatModel, MockChatModel]:
    if settings.USE_MOCK_LLM:
        return MockChatModel()
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=settings.TEMPERATURE,
    )

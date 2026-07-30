import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from app.graph.llm import get_llm
from app.graph.state import ActionItem, MeetingState

logger = logging.getLogger(__name__)

_MOCK_TRANSCRIPT = """
会议主题：新产品 V2.0 开发规划会议
时间：2025年7月28日 14:00-16:00
参会人员：张三（产品经理）、李四（技术负责人）、王五（设计师）、赵六（测试负责人）

张三：感谢大家参加今天的产品规划会议。今天主要讨论 V2.0 版本的三个核心议题：
产品定位、技术架构和上线计划。首先关于产品定位，我认为我们需要更聚焦于中小企业用户，
降低使用门槛并优化核心功能流程。

李四：我同意。从技术角度看，我们需要重新设计架构以支持更高的并发。建议采用微服务架构，
将用户服务、订单服务和支付服务拆分开来，这样每个服务可以独立扩展和部署。

王五：从设计角度，我们需要统一设计语言。我会在下周输出新的设计规范文档，
确保前端组件库的一致性。

张三：好的。关于上线时间，我建议 Q3 完成内测，Q4 正式上线。李四，技术侧能配合吗？

李四：如果采用微服务架构，开发周期大概需要 6 周。我需要在本月 20 号前完成技术架构文档，
然后团队可以开始开发。支付服务的对接可能需要额外 1 周。

赵六：测试这边，我建议在开发完成后预留 2 周的测试时间。我会制定详细的测试计划，
覆盖功能测试、性能测试和安全测试。

张三：好的，总结一下待办事项。张三负责完成产品原型设计，截止 8 月 15 日；
李四负责输出技术架构文档，截止 8 月 20 日；王五负责设计规范文档，截止 8 月 10 日；
赵六负责测试计划，截止 8 月 30 日。下次会议定在 8 月 5 日。
"""

_SPLIT_PROMPT = """你是一个会议记录分析助手。请将下面的会议记录按议题分割成多个文本块。

要求：
1. 识别不同的议题（如产品定位、技术架构、上线计划等）
2. 每个文本块应包含一个完整议题的讨论内容
3. 严格以 JSON 数组格式返回，数组中每个元素是一个字符串
4. 不要包含任何其他说明文字，只返回 JSON

会议记录：
{transcript}
"""

_SUMMARY_PROMPT = """你是一个会议纪要生成助手。基于以下分割后的会议议题文本块，生成一份结构化的会议摘要。

要求：
1. 概括每个议题的核心讨论点
2. 突出关键决策和结论
3. 语言简洁专业
4. 输出纯文本段落，不要使用 markdown 标题

议题文本块：
{segments}
"""

_ACTION_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_action_items",
        "description": "从会议记录中提取待办事项",
        "parameters": {
            "type": "object",
            "properties": {
                "action_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "待办事项内容"},
                            "owner": {"type": "string", "description": "负责人姓名"},
                            "deadline": {"type": "string", "description": "截止时间"},
                        },
                        "required": ["content", "owner", "deadline"],
                    },
                },
            },
            "required": ["action_items"],
        },
    },
}

_ACTION_PROMPT = """请从以下会议记录中提取所有待办事项（Action Items）。
必须通过调用 extract_action_items 工具返回结果，每个待办事项需包含内容、负责人和截止时间。

会议记录：
{transcript}
"""


def transcribe_node(state: MeetingState) -> Dict[str, Any]:
    """Mock ASR: returns a preset meeting transcript without calling any API."""
    logger.info("transcribe_node: generating mock transcript")
    return {"full_text": _MOCK_TRANSCRIPT.strip()}


def split_node(state: MeetingState) -> Dict[str, Any]:
    """Splits the full transcript into topic-based segments via DeepSeek."""
    logger.info("split_node: splitting transcript into segments")
    llm = get_llm()
    prompt = _SPLIT_PROMPT.format(transcript=state["full_text"])
    response = llm.invoke([HumanMessage(content=prompt)])
    segments = _parse_segments(response.content)
    logger.info("split_node: produced %d segments", len(segments))
    return {"segments": segments}


def summary_node(state: MeetingState) -> Dict[str, Any]:
    """Generates a structured meeting summary from the segments."""
    logger.info("summary_node: generating summary")
    llm = get_llm()
    segments_text = "\n\n".join(
        f"[议题 {i + 1}]\n{seg}" for i, seg in enumerate(state["segments"])
    )
    prompt = _SUMMARY_PROMPT.format(segments=segments_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"summary": response.content.strip()}


def action_node(state: MeetingState) -> Dict[str, Any]:
    """Extracts action items using DeepSeek function calling."""
    logger.info("action_node: extracting action items")
    llm = get_llm()
    llm_with_tools = llm.bind_tools([_ACTION_TOOL_SCHEMA])
    prompt = _ACTION_PROMPT.format(transcript=state["full_text"])
    response = llm_with_tools.invoke([HumanMessage(content=prompt)])
    action_items = _parse_action_items(response)
    logger.info("action_node: extracted %d action items", len(action_items))
    return {"action_items": action_items}


def _parse_segments(content: str) -> List[str]:
    """Robustly parses the LLM's JSON array response into a list of strings."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [str(item) for item in data]
    except json.JSONDecodeError:
        start, end = content.find("["), content.rfind("]")
        if start != -1 and end != -1:
            try:
                data = json.loads(content[start : end + 1])
                if isinstance(data, list):
                    return [str(item) for item in data]
            except json.JSONDecodeError:
                pass
    return [content]


def _parse_action_items(response: Any) -> List[ActionItem]:
    """Extracts action items from tool_calls, with a JSON content fallback."""
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        args = tool_calls[0].get("args", {})
        items = args.get("action_items", [])
        return [
            {
                "content": item.get("content", ""),
                "owner": item.get("owner", ""),
                "deadline": item.get("deadline", ""),
            }
            for item in items
        ]
    try:
        data = json.loads(response.content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "action_items" in data:
            return data["action_items"]
    except (json.JSONDecodeError, TypeError):
        pass
    return []

from typing import List

from pydantic import BaseModel, Field


class ActionItemResponse(BaseModel):
    content: str = Field(..., description="待办事项内容")
    owner: str = Field(..., description="负责人")
    deadline: str = Field(..., description="截止时间")


class ProcessMeetingRequest(BaseModel):
    transcript: str = Field(
        default="",
        description="会议记录文本，为空时使用内置 Mock 数据",
    )


class ProcessMeetingResponse(BaseModel):
    summary: str = Field(..., description="会议摘要")
    action_items: List[ActionItemResponse] = Field(..., description="待办事项列表")
    segments: List[str] = Field(default_factory=list, description="分割后的议题文本块")

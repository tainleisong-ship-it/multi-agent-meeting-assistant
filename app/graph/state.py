from typing import List, TypedDict


class ActionItem(TypedDict):
    content: str
    owner: str
    deadline: str


class MeetingState(TypedDict):
    full_text: str
    segments: List[str]
    summary: str
    action_items: List[ActionItem]

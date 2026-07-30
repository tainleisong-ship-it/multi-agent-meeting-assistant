from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    action_node,
    split_node,
    summary_node,
    transcribe_node,
)
from app.graph.state import MeetingState


def build_workflow():
    graph = StateGraph(MeetingState)
    graph.add_node("transcribe", transcribe_node)
    graph.add_node("split", split_node)
    graph.add_node("summary", summary_node)
    graph.add_node("action", action_node)

    graph.set_entry_point("transcribe")
    graph.add_edge("transcribe", "split")
    # Fan-out: summary and action run in parallel after split
    graph.add_edge("split", "summary")
    graph.add_edge("split", "action")
    graph.add_edge("summary", END)
    graph.add_edge("action", END)

    return graph.compile()


meeting_workflow = build_workflow()

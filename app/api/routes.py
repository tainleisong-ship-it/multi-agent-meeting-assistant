from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ActionItemResponse,
    ProcessMeetingRequest,
    ProcessMeetingResponse,
)
from app.graph.workflow import meeting_workflow

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/process", response_model=ProcessMeetingResponse)
async def process_meeting(request: ProcessMeetingRequest) -> ProcessMeetingResponse:
    try:
        initial_state = {"full_text": request.transcript} if request.transcript else {}
        result = meeting_workflow.invoke(initial_state)
        return ProcessMeetingResponse(
            summary=result.get("summary", ""),
            action_items=[
                ActionItemResponse(**item) for item in result.get("action_items", [])
            ],
            segments=result.get("segments", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

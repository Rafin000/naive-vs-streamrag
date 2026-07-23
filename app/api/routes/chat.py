import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, Metrics, Thinking, ToolCall
from app.services.agent_service import handle

router = APIRouter()


@router.post("/ask")
async def ask(request: ChatRequest) -> StreamingResponse:
    async def event_stream():
        async for piece in handle(request.session_id, request.query, request.path):
            if isinstance(piece, Metrics):
                yield f"event: metrics\ndata: {piece.model_dump_json()}\n\n"
            elif isinstance(piece, ToolCall):
                yield f"event: tool\ndata: {piece.model_dump_json()}\n\n"
            elif isinstance(piece, Thinking):
                yield f"event: thinking\ndata: {json.dumps({'token': piece.text})}\n\n"
            else:
                yield f"data: {json.dumps({'token': piece})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

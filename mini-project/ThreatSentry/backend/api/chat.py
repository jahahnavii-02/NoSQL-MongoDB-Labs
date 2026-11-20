from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.chat_service import (
    send_message,
    list_conversations,
    get_messages,
)

router = APIRouter(prefix="/api/chat", tags=["Local AI Chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: str | None = None


@router.post("/")
def chat(payload: ChatRequest):
    try:
        return send_message(
            message=payload.message,
            conversation_id=payload.conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unavailable: {type(exc).__name__}: {str(exc)[:200]}",
        )


@router.get("/conversations")
def conversations():
    try:
        return {"conversations": list_conversations()}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not load conversations: {type(exc).__name__}",
        )


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: str):
    try:
        return {
            "conversation_id": conversation_id,
            "messages": get_messages(conversation_id),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not load messages: {type(exc).__name__}",
        )



from fastapi.responses import StreamingResponse
from backend.services.chat_stream import stream_message


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    return StreamingResponse(
        stream_message(payload.message, payload.conversation_id),
        media_type="application/x-ndjson",
    )

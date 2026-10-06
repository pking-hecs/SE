from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.app import history_store

router = APIRouter(prefix="/history", tags=["Chat history"])


class ConversationCreate(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    project_id: int = 1


class MessageCreate(BaseModel):
    role: str
    text: str = Field(min_length=1)


@router.get("/")
async def list_history():
    return {"conversations": history_store.list_conversations()}


@router.post("/conversations")
async def create_history_conversation(payload: ConversationCreate):
    return history_store.create_conversation(payload.id, payload.title, payload.project_id)


@router.get("/conversations/{conversation_id}")
async def get_history_conversation(conversation_id: str):
    conversation = history_store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations/{conversation_id}/messages")
async def save_history_message(conversation_id: str, payload: MessageCreate):
    if payload.role not in {"user", "assistant"}:
        raise HTTPException(status_code=422, detail="role must be user or assistant")
    if not history_store.get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    history_store.add_message(conversation_id, payload.role, payload.text)
    return {"status": "saved"}


@router.delete("/conversations/{conversation_id}")
async def remove_history_conversation(conversation_id: str):
    if not history_store.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

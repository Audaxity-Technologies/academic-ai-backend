from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationMessageCreate, ConversationMessageResponse, ConversationThreadCreate,
    ConversationThreadResponse, ConversationWithMessages, ExplanationLevel,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationThreadResponse)
def create_conversation(body: ConversationThreadCreate, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    return ConversationService(db).create_thread(user, body.course_id, body.title)


@router.get("", response_model=list[ConversationThreadResponse])
def list_conversations(course_id: UUID | None = None, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    return ConversationService(db).list_threads(user, course_id)


@router.get("/{thread_id}", response_model=ConversationWithMessages)
def get_conversation(thread_id: UUID, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    service = ConversationService(db)
    thread = service.get_thread(thread_id, user)
    response = ConversationThreadResponse.model_validate(thread)
    return ConversationWithMessages(
        **response.model_dump(),
        messages=service.messages(thread),
    )


@router.post("/{thread_id}/messages", response_model=ConversationMessageResponse)
def add_message(thread_id: UUID, body: ConversationMessageCreate,
                explanation_level: ExplanationLevel | None = None,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.thread_id is not None and body.thread_id != thread_id:
        raise HTTPException(422, "Message thread does not match the URL")
    return ConversationService(db).add_message(thread_id, user, body.content, explanation_level)


@router.get("/{thread_id}/messages", response_model=list[ConversationMessageResponse])
def get_messages(thread_id: UUID, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = ConversationService(db)
    thread = service.get_thread(thread_id, user)
    return service.messages(thread, offset, limit)


@router.delete("/{thread_id}", status_code=204)
def delete_conversation(thread_id: UUID, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    ConversationService(db).delete_thread(thread_id, user)


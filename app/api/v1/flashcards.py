from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.flashcard import (
    CardContent, CardCreate, CardDeck, FlashcardResponse, GenerateCards, ReviewRequest, ReviewResponse,
)
from app.services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


@router.get("", response_model=CardDeck)
def deck(course_id: UUID, due_only: bool = False, topic_id: UUID | None = None,
         lecture_id: UUID | None = None, offset: int = Query(0, ge=0),
         limit: int = Query(100, ge=1, le=100),
         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).deck(course_id, due_only, offset, limit, topic_id, lecture_id)


@router.post("", response_model=FlashcardResponse, status_code=201)
def create(body: CardCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).create(body)


@router.post("/generate", response_model=list[FlashcardResponse], status_code=201)
def generate(body: GenerateCards, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).generate(body)


@router.put("/{card_id}", response_model=FlashcardResponse)
def update(card_id: UUID, body: CardContent,
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).update(card_id, body)


@router.delete("/{card_id}", status_code=204)
def delete(card_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    FlashcardService(db, user).remove(card_id)


@router.post("/{card_id}/reviews", response_model=FlashcardResponse)
def review(card_id: UUID, body: ReviewRequest,
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).review(card_id, body)


@router.get("/{card_id}/reviews", response_model=list[ReviewResponse])
def history(card_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FlashcardService(db, user).history(card_id)


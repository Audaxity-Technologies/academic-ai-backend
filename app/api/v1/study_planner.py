from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.schemas.study_plan import GoalCreate, GoalReplan, GoalResponse, SessionResponse, SessionUpdate
from app.services.study_plan_service import StudyPlanService

router = APIRouter(prefix="/study-planner", tags=["Study planner"])


@router.get("/goals", response_model=list[GoalResponse])
def list_goals(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return StudyPlanService(db, user).list_goals(course_id)


@router.post("/goals", response_model=GoalResponse, status_code=201)
def create(body: GoalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return StudyPlanService(db, user).create(body)


@router.post("/goals/{goal_id}/replan", response_model=GoalResponse)
def replan(goal_id: UUID, body: GoalReplan, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    return StudyPlanService(db, user).replan(goal_id, body)


@router.patch("/goals/{goal_id}/sessions/{session_id}", response_model=SessionResponse)
def complete(goal_id: UUID, session_id: UUID, body: SessionUpdate, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    return StudyPlanService(db, user).update_session(goal_id, session_id, body.completed)


@router.delete("/goals/{goal_id}", status_code=204)
def remove(goal_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    StudyPlanService(db, user).remove(goal_id)


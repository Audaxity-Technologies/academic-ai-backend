from fastapi import APIRouter, Depends

from app.database.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import MeResponse


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=MeResponse,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
    )
from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me")
async def get_current_user():
    return {
        "message": "Get current user"
    }


@router.put("/me")
async def update_current_user():
    return {
        "message": "Update current user"
    }
from fastapi import APIRouter

router = APIRouter(
    prefix="/institutions",
    tags=["Institutions"],
)


@router.get("/")
async def get_institutions():
    return {
        "message": "Get institutions"
    }


@router.post("/")
async def create_institution():
    return {
        "message": "Create institution"
    }
from fastapi import APIRouter

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.get("/")
async def get_departments():
    return {
        "message": "Get departments"
    }


@router.get("/{department_id}")
async def get_department(department_id: int):
    return {
        "message": "Get department",
        "department_id": department_id,
    }


@router.post("/")
async def create_department():
    return {
        "message": "Create department"
    }


@router.put("/{department_id}")
async def update_department(department_id: int):
    return {
        "message": "Update department",
        "department_id": department_id,
    }


@router.delete("/{department_id}")
async def delete_department(department_id: int):
    return {
        "message": "Delete department",
        "department_id": department_id,
    }
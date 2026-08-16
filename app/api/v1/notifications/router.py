from fastapi import APIRouter

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/")
async def get_notifications():
    return {
        "message": "Get notifications",
        "notifications": [],
    }


@router.get("/unread")
async def get_unread_notifications():
    return {
        "message": "Get unread notifications",
        "notifications": [],
    }


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    return {
        "message": "Notification marked as read",
        "notification_id": notification_id,
    }
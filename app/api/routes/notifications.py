from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_notification_repository
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationRead
from app.schemas.user import UserRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    user: UserRead = Depends(get_current_user),
    notifications: NotificationRepository = Depends(get_notification_repository),
) -> list[NotificationRead]:
    """Lists your notifications, newest first."""
    return await notifications.list_for_user(user.id)

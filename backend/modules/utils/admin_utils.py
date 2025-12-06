from fastapi import Depends, HTTPException, status

from modules.utils.jwt_utils import get_current_user
from modules.models.user import User


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return user

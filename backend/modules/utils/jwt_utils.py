import datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.utils.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def _create_token(data: dict, expire_delta: datetime.timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expire_delta
    to_encode.update({"exp": expire, "type": token_type})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        settings.ALGORITHM,
    )


def create_access_token(data: dict, expire_delta: datetime.timedelta) -> str:
    return _create_token(data=data, expire_delta=expire_delta, token_type="access")


def create_refresh_token(data: dict, expire_delta: datetime.timedelta) -> str:
    return _create_token(data=data, expire_delta=expire_delta, token_type="refresh")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
) -> User:

    if not token:
        token = request.query_params.get("access_token")
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        if payload.get("type") not in (None, "access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = int(payload.get("sub"))
    except HTTPException:
        raise
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

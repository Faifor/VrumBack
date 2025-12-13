from datetime import timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy import select

from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.schemas.user_schemas import UserCreate, UserRead
from modules.schemas.auth_schemas import Token
from modules.utils.config import settings
from modules.utils.document_security import (
    decrypt_user_fields,
    get_sensitive_data_cipher,
)
from modules.utils.jwt_utils import create_access_token
from modules.utils.password_utils import hash_password, verify_password


class AuthHandler:
    # ВАЖНО: тут указываем Depends, и используем обычный Session
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def _err(self, message: str, code: int = status.HTTP_400_BAD_REQUEST):
        raise HTTPException(status_code=code, detail=message)

    async def register(self, data: UserCreate) -> UserRead:
        # БЕЗ await, функция синхронная
        exists = self._get_user_by_email(data.email)
        if exists:
            self._err("User already exists")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role="user",
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return UserRead.model_validate(user)

    async def login(self, form: OAuth2PasswordRequestForm) -> Token:
        user = self._get_user_by_email(form.username)

        if not user or not verify_password(form.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        token = create_access_token(
            data={"sub": str(user.id)},
            expire_delta=expire,
        )

        return Token(access_token=token)

    async def me(self, current_user: User) -> UserRead:
        cipher = get_sensitive_data_cipher()
        decrypted_fields = decrypt_user_fields(current_user, cipher)
        payload = {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            **decrypted_fields,
        }
        return UserRead(**payload)

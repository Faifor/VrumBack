import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from modules.connection_to_db.database import get_session
from modules.models.password_reset_request import PasswordResetRequest
from modules.models.user import User
from modules.schemas.user_schemas import UserCreate, UserRead
from modules.schemas.auth_schemas import (
    PasswordResetConfirm,
    PasswordResetRequest as PasswordResetRequestSchema,
    Token,
)
from modules.utils.config import settings
from modules.utils.document_security import (
    decrypt_user_fields,
    get_sensitive_data_cipher,
)
from modules.utils.email_utils import send_password_reset_code
from modules.utils.jwt_utils import create_access_token
from modules.utils.password_utils import hash_password, verify_password


class AuthHandler:
    MAX_FAILED_LOGIN_ATTEMPTS = 3
    LOCKOUT_PERIOD = timedelta(seconds=20)
    PASSWORD_RESET_LOCKOUT = timedelta(
        seconds=settings.PASSWORD_RESET_LOCKOUT_SECONDS
    )
    PASSWORD_RESET_CODE_TTL = timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

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

        if user:
            self._ensure_not_locked(user)

        if not user or not verify_password(form.password, user.hashed_password):
            if user:
                self._register_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        self._reset_failed_attempts(user)

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

    async def request_password_reset(
        self, data: PasswordResetRequestSchema
    ) -> dict[str, str]:
        user = self._get_user_by_email(data.email)

        if not user:
            # Возвращаем тот же ответ, чтобы не выдавать существование пользователя
            return {"detail": "Если аккаунт существует, письмо уже отправлено"}

        reset_request = self._create_reset_request(user)

        try:
            send_password_reset_code(user.email, reset_request.code)
        except RuntimeError as exc:
            self._err(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

        return {"detail": "Письмо с кодом подтверждения отправлено"}

    async def reset_password(self, data: PasswordResetConfirm) -> dict[str, str]:
        user = self._get_user_by_email(data.email)
        if not user:
            self._err("Пользователь не найден", status.HTTP_404_NOT_FOUND)

        reset_request = self._get_active_reset_request(user.id)
        if not reset_request:
            self._err("Нет активного запроса на смену пароля")

        self._ensure_reset_attempts_allowed(reset_request)

        if reset_request.code != data.code:
            self._register_failed_reset_attempt(reset_request)
            self._err("Неверный код подтверждения")

        user.hashed_password = hash_password(data.new_password)
        reset_request.is_used = True
        reset_request.attempts = 0
        reset_request.locked_until = None
        self.session.commit()

        return {"detail": "Пароль успешно обновлен"}

    def _ensure_not_locked(self, user: User) -> None:
        if (
            user.failed_login_attempts < self.MAX_FAILED_LOGIN_ATTEMPTS
            or not user.last_failed_login_at
        ):
            return

        last_failed = user.last_failed_login_at
        if last_failed.tzinfo is None:
            last_failed = last_failed.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        elapsed = now - last_failed
        if elapsed < self.LOCKOUT_PERIOD:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много неуспешных попыток. Попробуйте позже.",
            )

        self._reset_failed_attempts(user)

    def _register_failed_login(self, user: User) -> None:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        user.last_failed_login_at = datetime.now(timezone.utc)
        self.session.commit()

    def _reset_failed_attempts(self, user: User) -> None:
        if user.failed_login_attempts == 0 and user.last_failed_login_at is None:
            return

        user.failed_login_attempts = 0
        user.last_failed_login_at = None
        self.session.commit()

    def _create_reset_request(self, user: User) -> PasswordResetRequest:
        expires_at = datetime.now(timezone.utc) + self.PASSWORD_RESET_CODE_TTL

        self.session.execute(
            update(PasswordResetRequest)
            .where(
                PasswordResetRequest.user_id == user.id,
                PasswordResetRequest.is_used.is_(False),
            )
            .values(is_used=True)
        )

        reset_request = PasswordResetRequest(
            user_id=user.id,
            code=f"{secrets.randbelow(1_000_000):06d}",
            expires_at=expires_at,
            attempts=0,
            locked_until=None,
        )

        self.session.add(reset_request)
        self.session.commit()
        self.session.refresh(reset_request)

        return reset_request

    def _get_active_reset_request(self, user_id: int) -> PasswordResetRequest | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(PasswordResetRequest)
            .where(
                PasswordResetRequest.user_id == user_id,
                PasswordResetRequest.is_used.is_(False),
                PasswordResetRequest.expires_at > now,
            )
            .order_by(PasswordResetRequest.created_at.desc())
        )
        result = self.session.execute(stmt)
        return result.scalars().first()

    def _ensure_reset_attempts_allowed(
        self, reset_request: PasswordResetRequest
    ) -> None:
        now = datetime.now(timezone.utc)

        if reset_request.expires_at <= now:
            reset_request.is_used = True
            self.session.commit()
            self._err("Срок действия кода истёк")

        if reset_request.locked_until:
            locked_until = reset_request.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if locked_until > now:
                remaining = int((locked_until - now).total_seconds())
                self._err(
                    f"Слишком много попыток. Попробуйте через {remaining} секунд.",
                    status.HTTP_429_TOO_MANY_REQUESTS,
                )

            reset_request.attempts = 0
            reset_request.locked_until = None
            self.session.commit()

    def _register_failed_reset_attempt(
        self, reset_request: PasswordResetRequest
    ) -> None:
        reset_request.attempts = (reset_request.attempts or 0) + 1

        if reset_request.attempts >= settings.PASSWORD_RESET_MAX_ATTEMPTS:
            reset_request.locked_until = datetime.now(timezone.utc) + self.PASSWORD_RESET_LOCKOUT
            reset_request.attempts = 0

        self.session.commit()

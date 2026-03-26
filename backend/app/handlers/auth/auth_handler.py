import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from modules.connection_to_db.database import get_session
from modules.models.email_verification_request import EmailVerificationRequest
from modules.models.password_reset_request import PasswordResetRequest
from modules.models.user import User
from modules.schemas.auth_schemas import (
    PasswordResetConfirm,
    PasswordResetRequest as PasswordResetRequestSchema,
    RegistrationCodeRequest,
    Token,
)
from modules.schemas.user_schemas import UserCreate, UserRead
from modules.utils.config import settings
from modules.utils.document_security import (
    decrypt_user_fields,
    get_sensitive_data_cipher,
)
from modules.utils.email_utils import (
    send_password_reset_code,
    send_registration_code,
)
from modules.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
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
    PASSWORD_RESET_RESEND_INTERVAL = timedelta(seconds=30)

    REGISTRATION_CODE_TTL = timedelta(minutes=10)
    REGISTRATION_LOCKOUT = timedelta(seconds=60)
    REGISTRATION_RESEND_INTERVAL = timedelta(seconds=30)
    REGISTRATION_PASSWORD_PATTERN = re.compile(
        r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[!\"№@#$%^&*()_+\-=\[\]{};':\\|,.<>/?`~:])[A-Za-z\d!\"№@#$%^&*()_+\-=\[\]{};':\\|,.<>/?`~:]{9,}$"
    )

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    def _err(self, message: str, code: int = status.HTTP_400_BAD_REQUEST):
        raise HTTPException(status_code=code, detail=message)

    async def request_registration_code(
        self, data: RegistrationCodeRequest
    ) -> dict[str, str]:
        if self._get_user_by_email(data.email):
            self._err("Пользователь с такой почтой уже зарегистрирован")

        self._ensure_registration_resend_allowed(data.email)
        verification = self._create_registration_request(data.email)

        try:
            send_registration_code(data.email, verification.code)
        except RuntimeError as exc:
            self._err(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

        return {"detail": "Письмо с кодом подтверждения отправлено"}

    async def register(self, data: UserCreate) -> UserRead:
        exists = self._get_user_by_email(data.email)
        if exists:
            self._err("User already exists")

        self._validate_registration_passwords(data.password, data.password_repeat)

        verification = self._get_active_registration_request(data.email)
        if not verification:
            self._err("Нет активного запроса на подтверждение почты")

        self._ensure_registration_attempts_allowed(verification)

        if verification.code != data.code:
            self._register_failed_registration_attempt(verification)
            self._err("Неверный код подтверждения")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role="user",
        )

        verification.is_used = True
        verification.attempts = 0
        verification.locked_until = None

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

        return self._build_token_pair(user.id)

    async def refresh(self, refresh_token: str) -> Token:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            user_id = int(payload.get("sub"))
        except HTTPException:
            raise
        except (JWTError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return self._build_token_pair(user.id)

    def _build_token_pair(self, user_id: int) -> Token:
        access_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": str(user_id)},
            expire_delta=access_expire,
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user_id)},
            expire_delta=refresh_expire,
        )

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def me(self, current_user: User) -> UserRead:
        cipher = get_sensitive_data_cipher()
        decrypted_fields = decrypt_user_fields(current_user, cipher)
        payload = {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role,
            "status": current_user.status,
            "rejection_reason": current_user.rejection_reason,
            **decrypted_fields,
        }
        return UserRead(**payload)

    async def request_password_reset(
        self, data: PasswordResetRequestSchema
    ) -> dict[str, str]:
        user = self._get_user_by_email(data.email)

        if not user:
            return {"detail": "Если аккаунт существует, письмо уже отправлено"}

        self._ensure_password_reset_resend_allowed(user.id)
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

    def _validate_registration_passwords(
        self, password: str, password_repeat: str
    ) -> None:
        if password != password_repeat:
            self._err("Пароли не совпадают")

        if not self.REGISTRATION_PASSWORD_PATTERN.match(password):
            self._err(
                "Пароль должен быть длиннее 8 символов, содержать английские буквы, минимум одну цифру и минимум один спецсимвол"
            )

    def _ensure_registration_resend_allowed(self, email: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(EmailVerificationRequest)
            .where(EmailVerificationRequest.email == email)
            .order_by(EmailVerificationRequest.created_at.desc())
        )
        last_request = self.session.execute(stmt).scalars().first()
        if not last_request:
            return

        created_at = last_request.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        allowed_at = created_at + self.REGISTRATION_RESEND_INTERVAL
        if now >= allowed_at:
            return

        remaining = int((allowed_at - now).total_seconds()) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Повторно запросить код можно через {remaining} секунд.",
        )

    def _create_registration_request(self, email: str) -> EmailVerificationRequest:
        expires_at = datetime.now(timezone.utc) + self.REGISTRATION_CODE_TTL

        self.session.execute(
            update(EmailVerificationRequest)
            .where(
                EmailVerificationRequest.email == email,
                EmailVerificationRequest.is_used.is_(False),
            )
            .values(is_used=True)
        )

        verification = EmailVerificationRequest(
            email=email,
            code=f"{secrets.randbelow(1_000_000):06d}",
            expires_at=expires_at,
            attempts=0,
            locked_until=None,
        )

        self.session.add(verification)
        self.session.commit()
        self.session.refresh(verification)

        return verification

    def _get_active_registration_request(
        self, email: str
    ) -> EmailVerificationRequest | None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(EmailVerificationRequest)
            .where(
                EmailVerificationRequest.email == email,
                EmailVerificationRequest.is_used.is_(False),
                EmailVerificationRequest.expires_at > now,
            )
            .order_by(EmailVerificationRequest.created_at.desc())
        )
        return self.session.execute(stmt).scalars().first()

    def _ensure_registration_attempts_allowed(
        self, verification: EmailVerificationRequest
    ) -> None:
        now = datetime.now(timezone.utc)

        if verification.expires_at <= now:
            verification.is_used = True
            self.session.commit()
            self._err("Срок действия кода истёк")

        if verification.locked_until:
            locked_until = verification.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if locked_until > now:
                remaining = int((locked_until - now).total_seconds())
                self._err(
                    f"Слишком много попыток. Попробуйте через {remaining} секунд.",
                    status.HTTP_429_TOO_MANY_REQUESTS,
                )

            verification.attempts = 0
            verification.locked_until = None
            self.session.commit()

    def _register_failed_registration_attempt(
        self, verification: EmailVerificationRequest
    ) -> None:
        verification.attempts = (verification.attempts or 0) + 1

        if verification.attempts >= settings.PASSWORD_RESET_MAX_ATTEMPTS:
            verification.locked_until = (
                datetime.now(timezone.utc) + self.REGISTRATION_LOCKOUT
            )
            verification.attempts = 0

        self.session.commit()

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

    def _ensure_password_reset_resend_allowed(self, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            select(PasswordResetRequest)
            .where(PasswordResetRequest.user_id == user_id)
            .order_by(PasswordResetRequest.created_at.desc())
        )
        last_request = self.session.execute(stmt).scalars().first()
        if not last_request:
            return

        created_at = last_request.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        allowed_at = created_at + self.PASSWORD_RESET_RESEND_INTERVAL
        if now >= allowed_at:
            return

        remaining = int((allowed_at - now).total_seconds()) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Повторно запросить код можно через {remaining} секунд.",
        )

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
            reset_request.locked_until = datetime.now(
                timezone.utc
            ) + self.PASSWORD_RESET_LOCKOUT
            reset_request.attempts = 0

        self.session.commit()

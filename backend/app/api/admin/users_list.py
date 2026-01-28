from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.handlers.admin.admin_handler import AdminHandler
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import UserWithDocumentSummary

router = APIRouter()


@router.get("/admin/users", response_model=list[UserWithDocumentSummary])
def admin_list_users(
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="all, approved, rejected, pending, draft",
    ),
    handler: AdminHandler = Depends(AdminHandler),
):
    if status_filter in (None, "all"):
        return handler.list_users()

    try:
        status_enum = DocumentStatusEnum(status_filter)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый статус",
        ) from exc

    return handler.list_users(status_enum)

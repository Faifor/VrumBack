from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.handlers.admin.admin_handler import AdminHandler

router = APIRouter()

_DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


@router.get("/admin/users/{user_id}/contract-docx/{document_id}")
def admin_get_user_contract_docx(
    user_id: int,
    document_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    buf = handler.get_contract_docx_bytes(user_id, document_id)
    filename = f"contract_{document_id}.docx"
    return StreamingResponse(
        buf,
        media_type=_DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

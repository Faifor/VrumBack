from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.handlers.admin.admin_handler import AdminHandler

router = APIRouter()

_DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


@router.get("/admin/users/{user_id}/return-acts/{act_id}/docx")
def admin_get_return_act_docx(
    user_id: int,
    act_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    buf = handler.get_return_act_docx_bytes(user_id, act_id)
    filename = f"return_act_{act_id}.docx"
    return StreamingResponse(
        buf,
        media_type=_DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

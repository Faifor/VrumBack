from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.handlers.admin.admin_handler import AdminHandler

router = APIRouter()


@router.get("/admin/users/{user_id}/contract-docx")
def admin_get_user_contract_docx(
    user_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    path = handler.get_contract_docx_path(user_id)
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=path.split("/")[-1],
    )

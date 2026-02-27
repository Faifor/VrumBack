from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.handlers.admin.admin_handler import AdminHandler

router = APIRouter()


@router.get("/admin/users/{user_id}/return-acts/{act_id}/docx")
def admin_get_return_act_docx(
    user_id: int,
    act_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    path = handler.get_return_act_docx_path(user_id, act_id)
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=path.split("/")[-1],
    )
from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler

router = APIRouter()


@router.get("/admin/ping")
def admin_ping(
    handler: AdminHandler = Depends(AdminHandler),
):
    admin = handler.admin
    return {"message": f"Hello, {admin.first_name}! Admin OK."}

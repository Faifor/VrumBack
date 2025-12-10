from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.utils.document_security import decrypt_user_fields

router = APIRouter()


@router.get("/admin/ping")
def admin_ping(
    handler: AdminHandler = Depends(AdminHandler),
):
    admin = handler.admin
    decrypted = decrypt_user_fields(admin, handler.cipher)
    greeting = decrypted.get("full_name") or admin.email
    return {"message": f"Hello, {greeting}! Admin OK."}

from fastapi import APIRouter

from .users_list import router as users_list_router
from .get_user_summary import router as get_user_summary_router
from .get_user_document import router as get_user_document_router
from .approve_document import router as approve_document_router
from .reject_document import router as reject_document_router
from .contract_docx import router as contract_docx_router
from .update_document import router as update_document_router
from .ping import router as ping_router

admin_router = APIRouter(tags=["Admin"])

admin_router.include_router(users_list_router)
admin_router.include_router(get_user_summary_router)
admin_router.include_router(get_user_document_router)
admin_router.include_router(approve_document_router)
admin_router.include_router(reject_document_router)
admin_router.include_router(contract_docx_router)
admin_router.include_router(update_document_router)
admin_router.include_router(ping_router)

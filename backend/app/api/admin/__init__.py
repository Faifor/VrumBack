from fastapi import APIRouter

from .users_list import router as users_list_router
from .get_user_summary import router as get_user_summary_router
from .get_user_document import router as get_user_document_router
from .approve_document import router as approve_document_router
from .reject_document import router as reject_document_router
from .contract_docx import router as contract_docx_router
from .list_user_contracts import router as list_user_contracts_router
from .update_document import router as update_document_router
from .ping import router as ping_router
from .sign_document import router as sign_document_router
from .user_payment_schedule import router as user_payment_schedule_router
from .inventory import router as inventory_router
from .return_acts import router as return_acts_router
from .return_act_docx import router as return_act_docx_router

admin_router = APIRouter()

admin_router.include_router(users_list_router, tags=["Admin Users"])
admin_router.include_router(get_user_summary_router, tags=["Admin Users"])
admin_router.include_router(get_user_document_router, tags=["Admin Documents"])
admin_router.include_router(approve_document_router, tags=["Admin Documents"])
admin_router.include_router(reject_document_router, tags=["Admin Documents"])
admin_router.include_router(contract_docx_router, tags=["Admin Contracts"])
admin_router.include_router(update_document_router, tags=["Admin Documents"])
admin_router.include_router(list_user_contracts_router, tags=["Admin Contracts"])
admin_router.include_router(ping_router, tags=["Admin System"])
admin_router.include_router(sign_document_router, tags=["Admin Contracts"])
admin_router.include_router(user_payment_schedule_router, tags=["Admin Payments"])
admin_router.include_router(inventory_router, tags=["Admin Inventory"])
admin_router.include_router(return_acts_router, tags=["Admin Contracts"])
admin_router.include_router(return_act_docx_router, tags=["Admin Contracts"])
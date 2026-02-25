from fastapi import APIRouter, Depends

from .get_document import router as get_document_router
from .update_document import router as update_document_router
from .submit_document import router as submit_document_router
from .contract_docx import router as contract_docx_router
from .list_contracts import router as list_contracts_router
from modules.utils.jwt_utils import get_current_user

user_document_router = APIRouter(dependencies=[Depends(get_current_user)])

user_document_router.include_router(get_document_router, tags=["User Documents"])
user_document_router.include_router(update_document_router, tags=["User Documents"])
user_document_router.include_router(submit_document_router, tags=["User Documents"])
user_document_router.include_router(contract_docx_router, tags=["User Contracts"])
user_document_router.include_router(list_contracts_router, tags=["User Contracts"])
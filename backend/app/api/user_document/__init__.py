from fastapi import APIRouter

from .get_document import router as get_document_router
from .update_document import router as update_document_router
from .submit_document import router as submit_document_router
from .contract_docx import router as contract_docx_router

user_document_router = APIRouter(tags=["User Document"])

user_document_router.include_router(get_document_router)
user_document_router.include_router(update_document_router)
user_document_router.include_router(submit_document_router)
user_document_router.include_router(contract_docx_router)

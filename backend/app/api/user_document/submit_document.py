from fastapi import APIRouter, Depends

from app.handlers.user_document.user_document_handler import UserDocumentHandler
from modules.schemas.document_schemas import UserDocumentRead

router = APIRouter()


@router.post("/users/me/document/submit", response_model=UserDocumentRead)
def submit_my_document(
    handler: UserDocumentHandler = Depends(UserDocumentHandler),
):
    return handler.submit_my_document()

from fastapi import APIRouter, Depends

from app.handlers.user_document.user_document_handler import UserDocumentHandler
from modules.schemas.document_schemas import UserDocumentRead

router = APIRouter()


@router.get("/users/me/document", response_model=UserDocumentRead)
def get_my_document(
    handler: UserDocumentHandler = Depends(UserDocumentHandler),
):
    return handler.get_my_document()

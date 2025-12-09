from fastapi import APIRouter, Depends

from app.handlers.user_document.user_document_handler import UserDocumentHandler
from modules.schemas.document_schemas import UserDocumentRead, UserDocumentUserUpdate

router = APIRouter()


@router.put("/users/me/document", response_model=UserDocumentRead)
def update_my_document(
    data: UserDocumentUserUpdate,
    handler: UserDocumentHandler = Depends(UserDocumentHandler),
):
    return handler.upsert_my_document(data)
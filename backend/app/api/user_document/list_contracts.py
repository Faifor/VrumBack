from fastapi import APIRouter, Depends

from app.handlers.user_document.user_document_handler import UserDocumentHandler
from modules.schemas.document_schemas import UserContractItem

router = APIRouter()


@router.get("/users/me/documents", response_model=list[UserContractItem])
def list_my_contracts(handler: UserDocumentHandler = Depends(UserDocumentHandler)):
    return handler.list_my_contracts()

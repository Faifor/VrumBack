from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.handlers.user_document.user_document_handler import UserDocumentHandler

router = APIRouter()


@router.get("/users/me/contract-docx")
def get_my_contract_docx(
    handler: UserDocumentHandler = Depends(UserDocumentHandler),
):
    path = handler.get_my_contract_docx_path()
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=path.split("/")[-1],
    )

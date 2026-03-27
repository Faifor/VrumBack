from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.handlers.user_document.user_document_handler import UserDocumentHandler

router = APIRouter()

_DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


@router.get("/users/me/contract-docx/{document_id}")
def get_my_contract_docx(
    document_id: int,
    handler: UserDocumentHandler = Depends(UserDocumentHandler),
):
    buf = handler.get_my_contract_docx_bytes(document_id)
    filename = f"contract_{document_id}.docx"
    return StreamingResponse(
        buf,
        media_type=_DOCX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

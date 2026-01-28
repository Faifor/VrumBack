from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_router
from app.api.auth import auth_router
from app.api.user_document import user_document_router


app = FastAPI(
    title="Bike API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_document_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

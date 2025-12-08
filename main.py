# from datetime import datetime, timedelta
# from typing import Optional, List
# from sqlalchemy import Enum
# import os

# from fastapi import FastAPI, Depends, HTTPException, status, Request
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse

# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from pydantic import BaseModel, EmailStr

# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     DateTime,
#     Text,
#     ForeignKey,
#     create_engine,
# )
# from sqlalchemy.orm import declarative_base, sessionmaker, Session
# from sqlalchemy.sql import func

# from docx import Document as DocxDocument
# from docx.text.paragraph import Paragraph

# # ================= НАСТРОЙКИ =================

# SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_ME"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# SQLALCHEMY_DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql+psycopg2://postgres:postgres@localhost:5432/bike_db",
# )

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     echo=False,
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# app = FastAPI(title="Auth + Profile + DOCX Contracts API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.mount("/static", StaticFiles(directory="static"), name="static")

# CONTRACT_DOCX_TEMPLATE_PATH = "static/contract_template.docx"
# GENERATED_CONTRACTS_DIR = "generated_contracts"
# os.makedirs(GENERATED_CONTRACTS_DIR, exist_ok=True)

# # домен / город
# CONTRACT_CITY = "Великий Новгород"


# # ================= МОДЕЛИ БД =========


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)

#     email = Column(String, unique=True, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)

#     first_name = Column(String, nullable=False)
#     last_name = Column(String, nullable=False)

#     role = Column(String, nullable=False, default="user")


# class DocumentStatusEnum(str):
#     DRAFT = "draft"
#     PENDING = "pending"
#     APPROVED = "approved"
#     REJECTED = "rejected"


# class UserDocument(Base):
#     __tablename__ = "user_documents"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

#     # базовые данные
#     full_name = Column(String, nullable=False)
#     address = Column(String, nullable=False)
#     passport = Column(String, nullable=False)
#     phone = Column(String, nullable=False)
#     bank_account = Column(String, nullable=True)

#     # новые поля для шаблона
#     contract_number = Column(String, nullable=True)  # {№_договора}
#     bike_serial = Column(String, nullable=True)  # {Серийный_номер_велик}
#     akb1_serial = Column(String, nullable=True)  # {Серийный_нормер_АКБ_1}
#     akb2_serial = Column(String, nullable=True)  # {Серийный_нормер_АКБ_2}
#     akb3_serial = Column(String, nullable=True)  # {Серийный_нормер_АКБ_3}
#     amount = Column(String, nullable=True)  # {Сумма}
#     amount_text = Column(String, nullable=True)  # {Сумма_пропись}
#     weeks_count = Column(Integer, nullable=True)  # {Кол_во_недель}
#     filled_date = Column(String, nullable=True)  # {Дата_заполнения}
#     end_date = Column(String, nullable=True)  # {Дат_конец_аренды}

#     status = Column(String, default=DocumentStatusEnum.DRAFT, nullable=False)
#     rejection_reason = Column(String, nullable=True)

#     contract_text = Column(Text, nullable=True)

#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# # ================= Pydantic-схемы =================


# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str
#     first_name: str
#     last_name: str


# class UserRead(BaseModel):
#     id: int
#     email: EmailStr
#     first_name: str
#     last_name: str
#     role: str

#     class Config:
#         orm_mode = True


# class UserUpdate(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None


# class Token(BaseModel):
#     access_token: str
#     token_type: str


# class TokenData(BaseModel):
#     sub: Optional[str] = None


# class DocumentStatus(str, Enum):
#     draft = "draft"
#     pending = "pending"
#     approved = "approved"
#     rejected = "rejected"


# class UserDocumentBase(BaseModel):
#     full_name: str
#     address: str
#     passport: str
#     phone: str
#     bank_account: Optional[str] = None

#     # новые поля
#     contract_number: Optional[str] = None
#     bike_serial: Optional[str] = None
#     akb1_serial: Optional[str] = None
#     akb2_serial: Optional[str] = None
#     akb3_serial: Optional[str] = None
#     amount: Optional[str] = None
#     amount_text: Optional[str] = None
#     weeks_count: Optional[int] = None
#     filled_date: Optional[str] = None
#     end_date: Optional[str] = None

# class UserDocumentUpdate(UserDocumentBase):
#     pass


# class UserDocumentRead(UserDocumentBase):
#     id: int
#     status: DocumentStatus
#     rejection_reason: Optional[str]
#     contract_text: Optional[str]

#     class Config:
#         orm_mode = True


# class DocumentRejectRequest(BaseModel):
#     reason: str


# class UserWithDocumentSummary(BaseModel):
#     id: int
#     email: EmailStr
#     first_name: str
#     last_name: str
#     role: str
#     document_status: Optional[DocumentStatus] = None

#     class Config:
#         orm_mode = True


# # ================= УТИЛИТЫ =================


# def get_db() -> Session:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (
#         expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def get_user_by_email(db: Session, email: str) -> Optional[User]:
#     return db.query(User).filter(User.email == email).first()


# def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
#     user = get_user_by_email(db, email)
#     if not user or not verify_password(password, user.hashed_password):
#         return None
#     return user


# async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Не удалось проверить токен",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     token = None

#     auth_header = request.headers.get("Authorization")
#     if auth_header and auth_header.startswith("Bearer "):
#         token = auth_header.split(" ", 1)[1]
#     else:
#         token = request.query_params.get("access_token")

#     if not token:
#         raise credentials_exception

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         sub = payload.get("sub")
#         user_id = int(sub)
#     except Exception:
#         raise credentials_exception

#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise credentials_exception
#     return user


# async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
#     if current_user.role != "admin":
#         raise HTTPException(403, "Требуются права администратора")
#     return current_user


# # ================= DOCX: замена плейсхолдеров =================


# def _replace_in_paragraph(paragraph: Paragraph, values: dict):
#     """
#     Безопасная замена плейсхолдеров в параграфе с учётом того,
#     что Word рвёт текст на несколько runs.
#     """
#     if not paragraph.runs:
#         return

#     full_text = "".join(run.text for run in paragraph.runs)

#     new_text = full_text
#     for key, val in values.items():
#         placeholder = f"{{{key}}}"
#         if placeholder in new_text:
#             new_text = new_text.replace(placeholder, val)

#     if new_text == full_text:
#         return

#     paragraph.runs[0].text = new_text
#     for run in paragraph.runs[1:]:
#         run.text = ""


# def _replace_placeholders_in_docx(doc: DocxDocument, values: dict):
#     # параграфы основного тела документа
#     for paragraph in doc.paragraphs:
#         _replace_in_paragraph(paragraph, values)

#     # таблицы
#     for table in doc.tables:
#         for row in table.rows:
#             for cell in row.cells:
#                 for paragraph in cell.paragraphs:
#                     _replace_in_paragraph(paragraph, values)

#     # заголовки / колонтитулы (если туда тоже положишь плейсхолдеры)
#     for section in doc.sections:
#         header = section.header
#         for paragraph in header.paragraphs:
#             _replace_in_paragraph(paragraph, values)

#         footer = section.footer
#         for paragraph in footer.paragraphs:
#             _replace_in_paragraph(paragraph, values)


# def _week_word(n: Optional[int]) -> str:
#     """
#     Возвращает правильную форму слова "неделя" для плейсхолдера {неделю}
#     1 -> "неделю"
#     2,3,4 -> "недели"
#     5+ -> "недель"
#     """
#     if n is None:
#         return ""
#     n_abs = abs(n)
#     last_two = n_abs % 100
#     last = n_abs % 10
#     if 11 <= last_two <= 14:
#         return "недель"
#     if last == 1:
#         return "неделю"
#     if 2 <= last <= 4:
#         return "недели"
#     return "недель"


# def render_contract_docx(user: User, doc: UserDocument) -> str:
#     if not os.path.exists(CONTRACT_DOCX_TEMPLATE_PATH):
#         raise FileNotFoundError("DOCX-шаблон не найден")

#     document = DocxDocument(CONTRACT_DOCX_TEMPLATE_PATH)

#     today_str = datetime.utcnow().strftime("%d.%m.%Y")
#     week_word = _week_word(doc.weeks_count)

#     values = {
#         # базовые
#         "CITY": CONTRACT_CITY,
#         "DATE": today_str,
#         "FULL_NAME": doc.full_name or "",
#         "ФИО": doc.full_name or "",
#         "ADDRESS": doc.address or "",
#         "PASSPORT": doc.passport or "",
#         "PHONE": doc.phone or "",
#         "EMAIL": user.email or "",
#         "BANK_ACCOUNT": doc.bank_account or "-",
#         # договор и приложения
#         "№_договора": doc.contract_number or "",
#         "Номер_приложения": "1",  # если нужно сделать динамическим — вынести в БД
#         # серийники
#         "Серийный_номер_велик": doc.bike_serial or "",
#         "Серийный_нормер_АКБ_1": doc.akb1_serial or "",
#         "Серийный_нормер_АКБ_2": doc.akb2_serial or "",
#         "Серийный_нормер_АКБ_3": doc.akb3_serial or "",
#         # деньги + срок
#         "Сумма": doc.amount or "",
#         "Сумма_пропись": doc.amount_text or "",
#         "Кол_во_недель": str(doc.weeks_count) if doc.weeks_count is not None else "",
#         "неделю": week_word,
#         # даты периода аренды
#         "Дата_заполнения": doc.filled_date or today_str,
#         "Дат_конец_аренды": doc.end_date or "",
#     }

#     _replace_placeholders_in_docx(document, values)

#     out_path = os.path.join(GENERATED_CONTRACTS_DIR, f"contract_user_{user.id}.docx")
#     document.save(out_path)
#     return out_path


# # ================= ИНИЦИАЛИЗАЦИЯ БД =================


# def init_db():
#     Base.metadata.create_all(bind=engine)

#     db = SessionLocal()
#     try:
#         admin_email = "admin@example.com"
#         admin_pass = "admin123"

#         admin = get_user_by_email(db, admin_email)
#         if not admin:
#             admin = User(
#                 email=admin_email,
#                 hashed_password=get_password_hash(admin_pass),
#                 first_name="Roman",
#                 last_name="Romanov",
#                 role="admin",
#             )
#             db.add(admin)
#             db.commit()
#     finally:
#         db.close()


# init_db()


# # ================= AUTH =================


# @app.post("/auth/register", response_model=UserRead, status_code=201)
# def register(user_in: UserCreate, db: Session = Depends(get_db)):
#     if get_user_by_email(db, user_in.email):
#         raise HTTPException(400, "Пользователь уже существует")

#     user = User(
#         email=user_in.email,
#         hashed_password=get_password_hash(user_in.password),
#         first_name=user_in.first_name,
#         last_name=user_in.last_name,
#         role="user",
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user


# @app.post("/auth/login", response_model=Token)
# def login(
#     form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
# ):
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(400, "Неверный email или пароль")

#     token = create_access_token({"sub": str(user.id)})
#     return {"access_token": token, "token_type": "bearer"}


# @app.get("/auth/me", response_model=UserRead)
# def read_me(current_user: User = Depends(get_current_user)):
#     return current_user


# # ================= USER DOCUMENT =================


# @app.get("/users/me/document", response_model=UserDocumentRead)
# def get_my_document(
#     current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")
#     return doc


# @app.put("/users/me/document", response_model=UserDocumentRead)
# def upsert_my_document(
#     data: UserDocumentUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).first()
#     if not doc:
#         doc = UserDocument(
#             user_id=current_user.id,
#             full_name=data.full_name,
#             address=data.address,
#             passport=data.passport,
#             phone=data.phone,
#             bank_account=data.bank_account,
#             contract_number=data.contract_number,
#             bike_serial=data.bike_serial,
#             akb1_serial=data.akb1_serial,
#             akb2_serial=data.akb2_serial,
#             akb3_serial=data.akb3_serial,
#             amount=data.amount,
#             amount_text=data.amount_text,
#             weeks_count=data.weeks_count,
#             filled_date=data.filled_date,
#             end_date=data.end_date,
#             status=DocumentStatusEnum.DRAFT,
#         )
#         db.add(doc)
#     else:
#         doc.full_name = data.full_name
#         doc.address = data.address
#         doc.passport = data.passport
#         doc.phone = data.phone
#         doc.bank_account = data.bank_account

#         doc.contract_number = data.contract_number
#         doc.bike_serial = data.bike_serial
#         doc.akb1_serial = data.akb1_serial
#         doc.akb2_serial = data.akb2_serial
#         doc.akb3_serial = data.akb3_serial
#         doc.amount = data.amount
#         doc.amount_text = data.amount_text
#         doc.weeks_count = data.weeks_count
#         doc.filled_date = data.filled_date
#         doc.end_date = data.end_date

#         doc.status = DocumentStatusEnum.DRAFT
#         doc.rejection_reason = None
#         doc.contract_text = None

#     db.commit()
#     db.refresh(doc)
#     return doc


# @app.post("/users/me/document/submit", response_model=UserDocumentRead)
# def submit_my_document(
#     current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).first()
#     if not doc:
#         raise HTTPException(400, "Сначала заполните документ")

#     doc.status = DocumentStatusEnum.PENDING
#     doc.rejection_reason = None

#     db.commit()
#     db.refresh(doc)
#     return doc


# # ================= USER CONTRACT DOCX =================


# @app.get("/users/me/contract-docx")
# def get_my_contract_docx(
#     current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")

#     if doc.status != DocumentStatusEnum.APPROVED:
#         raise HTTPException(400, "Договор еще не одобрен")

#     path = render_contract_docx(current_user, doc)

#     return FileResponse(
#         path,
#         media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#         filename=f"contract_{current_user.id}.docx",
#     )


# # ================= ADMIN =================


# @app.get("/admin/users", response_model=List[UserWithDocumentSummary])
# def admin_list_users(
#     admin: User = Depends(get_current_admin), db: Session = Depends(get_db)
# ):
#     users = db.query(User).filter(User.role == "user").all()
#     result: List[UserWithDocumentSummary] = []

#     for u in users:
#         doc = db.query(UserDocument).filter(UserDocument.user_id == u.id).first()
#         result.append(
#             UserWithDocumentSummary(
#                 id=u.id,
#                 email=u.email,
#                 first_name=u.first_name,
#                 last_name=u.last_name,
#                 role=u.role,
#                 document_status=DocumentStatus(doc.status) if doc else None,
#             )
#         )

#     return result


# @app.get("/admin/users/{user_id}/document", response_model=UserDocumentRead)
# def admin_get_user_document(
#     user_id: int,
#     admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")
#     return doc


# @app.post("/admin/users/{user_id}/document/approve", response_model=UserDocumentRead)
# def admin_approve_document(
#     user_id: int,
#     admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")

#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(404, "Пользователь не найден")

#     doc.status = DocumentStatusEnum.APPROVED
#     doc.rejection_reason = None
#     doc.contract_text = "Договор успешно сформирован"

#     db.commit()
#     db.refresh(doc)
#     return doc


# @app.post("/admin/users/{user_id}/document/reject", response_model=UserDocumentRead)
# def admin_reject_document(
#     user_id: int,
#     data: DocumentRejectRequest,
#     admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")

#     doc.status = DocumentStatusEnum.REJECTED
#     doc.rejection_reason = data.reason
#     doc.contract_text = None

#     db.commit()
#     db.refresh(doc)
#     return doc


# @app.get("/admin/users/{user_id}/contract-docx")
# def admin_get_user_contract_docx(
#     user_id: int,
#     admin: User = Depends(get_current_admin),
#     db: Session = Depends(get_db),
# ):
#     doc = db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
#     if not doc:
#         raise HTTPException(404, "Документ не найден")

#     if doc.status != DocumentStatusEnum.APPROVED:
#         raise HTTPException(400, "Договор еще не одобрен")

#     user = db.query(User).filter(User.id == user_id).first()

#     path = render_contract_docx(user, doc)

#     return FileResponse(
#         path,
#         media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#         filename=f"contract_{user_id}.docx",
#     )


# @app.get("/admin/ping")
# def admin_ping(admin: User = Depends(get_current_admin)):
#     return {"message": f"Hello, {admin.first_name}! Admin OK."}

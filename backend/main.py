import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import SessionLocal, engine, get_db
import backend.models as models
from backend.schemas import RegisterSchema, LoginSchema, ConversationSchema, MessageSchema
import backend.auth as auth
import backend.ai_service as ai_service
import backend.rag_service as rag_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
models.Base.metadata.create_all(bind=engine)

# add conversation_id to documents if db was created before this column existed
with engine.connect() as conn:
    conn.execute(text(
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS conversation_id BIGINT REFERENCES conversations(id)"
    ))
    conn.commit()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://ai-assistant-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(models.User).filter(models.User.email == payload["sub"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/auth/register")
def register(payload: RegisterSchema, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists"
        )

    user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=auth.hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.post("/auth/login")
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth.create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/conversations")
def create_conversation(
    payload: ConversationSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = models.Conversation(
        user_id=current_user.id,
        title=payload.title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "message": "Conversation created successfully",
        "conversation": {
            "id": conversation.id,
            "title": conversation.title
        }
    }


@app.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversations = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()
    return {
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at
            }
            for conversation in conversations
        ]
    }


@app.post("/conversations/{id}/messages")
def send_message(
    id: int,
    payload: MessageSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == id,
        models.Conversation.user_id == current_user.id
    ).first()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    user_message = models.Message(
        conversation_id=conversation.id,
        content=payload.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    doc_ids = [
        doc.id for doc in db.query(models.Document).filter(
            models.Document.conversation_id == conversation.id
        ).all()
    ]

    try:
        if doc_ids:
            assistant_text = rag_service.ask_with_rag(doc_ids, payload.message)
        else:
            assistant_text = ai_service.generate_response(payload.message)
    except Exception as e:
        assistant_text = f"Sorry, something went wrong: {str(e)}"
    assistant_message = models.Message(
        conversation_id=conversation.id,
        content=assistant_text
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "message": "Message sent successfully",
        "conversation_id": conversation.id,
        "assistant_response": assistant_text
    }


@app.get("/conversations/{id}/messages")
def get_messages(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == id,
        models.Conversation.user_id == current_user.id
    ).first()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = db.query(models.Message).filter(models.Message.conversation_id == conversation.id).all()
    return {
        "conversation_id": conversation.id,
        "messages": [
            {
                "id": message.id,
                "content": message.content,
                "created_at": message.created_at
            }
            for message in messages
        ]
    }


@app.delete("/conversations/{id}")
def delete_conversation(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == id,
        models.Conversation.user_id == current_user.id
    ).first()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.query(models.Message).filter(models.Message.conversation_id == conversation.id).delete()
    db.delete(conversation)
    db.commit()

    return {"message": f"Conversation {id} deleted successfully"}


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if conversation_id:
        conv = db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id,
            models.Conversation.user_id == current_user.id
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    uploads_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    safe_name = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(uploads_dir, safe_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    document = models.Document(
        user_id=current_user.id,
        conversation_id=conversation_id,
        file_name=file.filename,
        file_path=file_path
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        index_result = rag_service.process_document(document.id, file_path)
    except Exception as e:
        index_result = {"indexed": False, "message": str(e)}

    return {
        "message": "Document uploaded successfully",
        "document": {
            "id": document.id,
            "file_name": document.file_name,
            "conversation_id": document.conversation_id,
        },
        "indexing": index_result,
    }


@app.post("/rag/documents")
def chat_with_documents(
    payload: MessageSchema,
    conversation_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Document).filter(models.Document.user_id == current_user.id)

    if conversation_id:
        query = query.filter(models.Document.conversation_id == conversation_id)

    documents = query.all()
    doc_ids = [doc.id for doc in documents]
    document_names = [doc.file_name for doc in documents]

    if not doc_ids:
        ai_response = ai_service.generate_response(payload.message)
    else:
        ai_response = rag_service.ask_with_rag(doc_ids, payload.message)

    return {
        "message": ai_response,
        "documents": document_names
    }


@app.get("/conversations/{id}/documents")
def get_conversation_documents(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == id,
        models.Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    docs = db.query(models.Document).filter(
        models.Document.conversation_id == id
    ).all()

    return {
        "documents": [
            {"id": d.id, "file_name": d.file_name}
            for d in docs
        ]
    }

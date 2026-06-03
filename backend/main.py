import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine, get_db
import backend.models as models
from backend.schemas import RegisterSchema, LoginSchema, ConversationSchema, MessageSchema
import backend.auth as auth
import backend.ai_service as ai_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
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
        role="user",
        content=payload.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    assistant_text = ai_service.generate_response(payload.message)
    assistant_message = models.Message(
        conversation_id=conversation.id,
        role="assistant",
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
                "role": message.role,
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    uploads_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    file_path = os.path.join(uploads_dir, str(file.filename))
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    document = models.Document(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded successfully",
        "document": {
            "id": document.id,
            "file_name": document.file_name
        }
    }


@app.post("/rag/documents")
def chat_with_documents(
    payload: MessageSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    documents = db.query(models.Document).filter(models.Document.user_id == current_user.id).all()
    document_names = [str(doc.file_name) for doc in documents]

    if document_names:
        doc_list = ", ".join(document_names)
        prompt = f"User asked: {payload.message}\nUse these documents: {doc_list}"
    else:
        prompt = payload.message

    ai_response = ai_service.generate_response(prompt)
    return {
        "message": ai_response,
        "documents": document_names
    }

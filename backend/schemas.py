from pydantic import BaseModel


class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str


class LoginSchema(BaseModel):
    email: str
    password: str


class ConversationSchema(BaseModel):
    title: str


class MessageSchema(BaseModel):
    message: str


class ChatSchema(BaseModel):
    conversation_id: int
    message: str
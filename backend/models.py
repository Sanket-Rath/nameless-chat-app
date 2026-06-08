from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime

from sqlalchemy.sql import func

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)

    username = Column(String(50))

    email = Column(String(255))

    password_hash = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(BigInteger, primary_key=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id")
    )

    title = Column(String(255))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True)

    conversation_id = Column(
        BigInteger,
        ForeignKey("conversations.id")
    )

    content = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id")
    )

    conversation_id = Column(
        BigInteger,
        ForeignKey("conversations.id"),
        nullable=True
    )

    file_name = Column(String(255))

    file_path = Column(Text)

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from Security.dbBase import Base
import uuid


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # relationships
    chats = relationship("ChatModel", back_populates="user", cascade="all, delete")


class ChatModel(Base):
    __tablename__ = "chats"

    # Use string UUIDs for chat IDs so they can be passed as strings from the frontend
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

    user = relationship("UserModel", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete")


class ChatMessage(Base):
    __tablename__ = "messages"

    # Use a UUID string as primary key by default so inserts create an id when none is provided
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    # chat_id references ChatModel.id which is now a string UUID
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    image = Column(Text, nullable=True)  # base64-encoded image, if any
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)

    chat = relationship("ChatModel", back_populates="messages")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    rating = Column(Integer)  # 1 – 5
    comment = Column(Text)
    model = Column(String)
    prompt = Column(String)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
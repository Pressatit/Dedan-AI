from database import Base
from sqlalchemy import Column,String,Integer,DateTime,ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship




class User(Base):
    __tablename__='users'

    id=Column(Integer,primary_key=True,index=True)
    email=Column(String)
    name=Column(String)
    password=Column(String)
    created_at=Column(DateTime,server_default=func.now(),nullable=False)

    Session = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    Conversation=relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__='sessions'

    session_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at=Column(DateTime,server_default=func.now(),nullable=False)
    expires_at=Column(DateTime(timezone=True), nullable=False)
 
    user = relationship("User", back_populates="Session")




class Conversation(Base):
    __tablename__='conversations'

    conversation_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    started_at=Column(DateTime,server_default=func.now(),nullable=False)
    title=Column(String)
    data=Column(String)

    user = relationship("User", back_populates="Conversation")

    Messages=relationship(
        "Message",
        back_populates="Conversation",
        cascade="all, delete-orphan")

class Message(Base):

    __tablename__='messages'

    id=Column(Integer,primary_key=True,index=True,nullable=False)
    conversation_id=Column(Integer,ForeignKey("conversations.conversation_id"),nullable=False)
    sender=Column(String)
    content=Column(String)
    created_at=Column(DateTime,server_default=func.now(),nullable=False)

    Conversation=relationship("Conversation",back_populates="Messages")
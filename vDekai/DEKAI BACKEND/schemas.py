from pydantic import BaseModel
from datetime import datetime
from typing import List,Optional


#session
class SessionBase(BaseModel):
    expires_at: datetime

class SessionCreate(SessionBase):
    pass

class SessionOut(SessionBase):
    session_id: int
    token: str
    created_at: datetime

    class Config:
        from_attributes = True


#Conversation
class Conversation(BaseModel):
    title: str 

    class Config:
        from_attributes = True

#user
class User(BaseModel):
    email :str
    name : str
    password :str

    
class ShowUser(BaseModel):
    email : str
    name : str
    Conversation:List[Conversation]


    class Config():
        from_attributes = True

class userConversation(BaseModel):
    email: str
    name : str

    class Config():
        from_attributes = True

    
class ShowConversation(BaseModel):
   conversation_id: int
   title: str
   data: str
   user: userConversation
   started_at: datetime

   class Config():
       from_attributes= True
       
class ConversationOut(BaseModel):
    conversation_id: int
    title: str
    data: Optional[str]


    class Config:
        from_attributes = True
#Message
class Message(BaseModel):
    sender:str
    content: str
    

class showMessage(BaseModel):
    sender: str
    content: str
    created_at: datetime

    class Config():
        from_attributes=True


#Login
class Login(BaseModel):
    email: str
    password: str

#Token
class Token(BaseModel):
    access_token: str
    token_type: str

class GenerateRequest(BaseModel):
    prompt: str
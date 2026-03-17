from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
import schemas,models
from database import sessionmk
from typing import List
import oath2 

def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()

router=APIRouter(
    tags=['messages'],
    prefix="/message"
)


@router.post('')
def new_message(request: schemas.Message,db:Session=Depends(get_db),current_user:schemas.User=Depends(oath2.get_current_user)):
    new_message=models.Message(sender=request.sender,content=request.content,conversation_id=1)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return request



@router.get("/{conversation_id}/messages", response_model=List[schemas.showMessage])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(oath2.get_current_user)):
    conv = db.query(models.Conversation).filter(models.Conversation.conversation_id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.created_at.asc()).all()


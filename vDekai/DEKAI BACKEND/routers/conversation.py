from fastapi import APIRouter,Depends,HTTPException,status,requests
from sqlalchemy.orm import Session
import schemas,models
from database import sessionmk
import oath2
from datetime import datetime,timezone
from utils import title

def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()

router=APIRouter(
    tags=['conversations'],
    prefix="/conversation"
)


# get all conversations(admin)
@router.get('',response_model=list[schemas.ShowConversation])
def get_conversations(db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
    conversation=db.query(models.Conversation).all()
    return conversation

# get all conversations(specific user)
@router.get('/my',response_model=list[schemas.ShowConversation])
def get_my_conversations(db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
    conversations = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()
    return conversations

#get conversation    
@router.get('/{id}',response_model=schemas.ShowConversation)
def get_single_conversation(id,db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
    
    user=db.query(models.Conversation).filter(models.Conversation.conversation_id==id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Id {id} not found")
    
    return user


#create conversation api
@router.post('')
def create_conversation(db: Session = Depends(get_db),current_user: schemas.User = Depends(oath2.get_current_user)):

    new_conversation = models.Conversation(
        title="new_chat",
        data="",
        user_id=current_user.id
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)


    return new_conversation



#Delete conversation api
@router.delete('/{id}')
def del_conversation(id,db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
    del_conv=db.query(models.Conversation).filter(models.Conversation.conversation_id==id).delete(synchronize_session=False)
    if not del_conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Conversation Id {id} not found")
    
    db.commit()
    return {f"data:Conversation {id} has been deleted successfully"}

#Update conversation api
@router.put('/{id}')
def update_conversation(id,request: schemas.Conversation,db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
   update=db.query(models.Conversation).filter(models.Conversation.conversation_id==id).update({'title':request.title,'data':request.data})

   if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Conversation Id {id} not found")
    
   db.commit()
   return {'data:Updated'}
    
#delete messages
@router.delete('')
def clear_conversations(db:Session=Depends(get_db),current_user: schemas.User=Depends(oath2.get_current_user)):
    clear=db.query(models.Conversation).delete(synchronize_session=False)
    db.commit()

    return {'data':'Conversation completely erased ...finished'}


@router.post("/{conversation_id}/messages", response_model=schemas.Message)
def create_message(conversation_id: int, message: schemas.Message,
                   db: Session = Depends(get_db),
                   current_user: schemas.User = Depends(oath2.get_current_user)):

    # Ensure conversation exists and belongs to current user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.conversation_id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create message
    new_message = models.Message(
        sender=message.sender,
        content=message.content,
        conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc)
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    if conversation.title == "New conversation" and message.sender == "user":
        conversation.title = title.generate_conversation_title(message.content)
        db.commit()

    return new_message
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
import schemas,models
from database import sessionmk
from Hashing import Hash

router=APIRouter(
    tags=['users'],
    prefix='/user'
)

def get_db():
    db=sessionmk()
    try:
        yield db
    finally:
        db.close()


# get all users
@router.get('',response_model=list[schemas.ShowUser])
def get_operation(db:Session=Depends(get_db)):
    users=db.query(models.User).all()
    return users

 #get user    
@router.get('/{id}',response_model=schemas.ShowUser)
def get_single(id,db:Session=Depends(get_db)):
    
    user=db.query(models.User).filter(models.User.id==id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Id {id} not found")
    
    return user


#create user api
@router.post('')
def create_user(request: schemas.User,db:Session=Depends(get_db)):

    new_user=models.User(email=request.email,name=request.name,password=Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return request


#Delete user api
@router.delete('/{id}')
def del_user(id,db:Session=Depends(get_db)):
    del_user=db.query(models.User).filter(models.User.id==id).delete(synchronize_session=False)
    if not del_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Id {id} not found")
    
    db.commit()
    return {f"data:User {id} has been deleted successfully"}

#Update user api
@router.put('/{id}')
def Update_user(id,request: schemas.User,db:Session=Depends(get_db)):
   update=db.query(models.User).filter(models.User.id==id).update({'name':request.name,'email':request.email})

   if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Id {id} not found")
    
   db.commit()
   return {'data:Updated'}

'''
#Update password
@App.put('/user/{id}')
def Update_user(id,request: schemas.User,db:Session=Depends(get_db)):
   update=db.query(models.User).filter(models.User.id==id).update({'password:updated password'})

   if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Id {id} not found")
    
   db.commit()
   return {'data:password updated'}
'''
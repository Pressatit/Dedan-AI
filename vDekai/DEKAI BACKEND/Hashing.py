from passlib.context import CryptContext

pswd_cxt=CryptContext(schemes=["bcrypt"],deprecated="auto")

class Hash():
 def bcrypt(password : str):
    hashed_password=pswd_cxt.hash(password)

    return hashed_password
 
 def verify(hashed_password, plain_password):
        return pswd_cxt.verify(plain_password, hashed_password)
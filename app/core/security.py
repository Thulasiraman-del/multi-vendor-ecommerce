from datetime import timezone,timedelta,datetime
from jose import jwt


from pwdlib import PasswordHash
password_hasher=PasswordHash.recommended()
SECRETE_KEY="change-this-secrete-key"
ALGORITHM="HS256"   
ACCESS_TOKEN_EXPIRE_MINUTES=30
def hash_password(password:str)->str:
    return password_hasher.hash(password)
def verify_password(password:str,hashed_password:str)->bool:
    return password_hasher.verify(password,hashed_password)
def create_access_token(data:dict,expires_delta:int|None=None)->str:
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRETE_KEY,algorithm=ALGORITHM)
def decode_access_token(token:str)->dict:
    try:
        payload=jwt.decode(token,SECRETE_KEY,algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
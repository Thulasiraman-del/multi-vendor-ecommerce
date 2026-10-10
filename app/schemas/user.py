from pydantic import BaseModel, ConfigDict,EmailStr
class UserCreate(BaseModel):
    email:EmailStr
    full_name:str
    password:str
    phone:str|None=None
class UserResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    email:EmailStr
    full_name:str
    phone:str|None=None
    is_active:bool
    role:str
class UserLogin(BaseModel):
    email:EmailStr
    password:str
class TokenResponse(BaseModel):
    access_token:str
    token_type:str
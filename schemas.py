from typing import Optional
from pydantic import BaseModel,EmailStr

class createUser(BaseModel):
    email: EmailStr
    password: str
    token: Optional[str]=None

    
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes= True
class UserLogin(BaseModel):
    email: str
    password: str
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    email: Optional[str]=None
    
class CreateComment(BaseModel):
    comment: str
    score: Optional[str]=None
    id_user: int
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel,EmailStr
from database import Base, engine, sessionLocal
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import Session
from models import User,Avis
from schemas import createUser, UserLogin, UserResponse, Token, TokenData, CreateComment
import secrets
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated, List, Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
SECRET_KEY= os.getenv('SECRET_KEY')
ALGORITHM= os.getenv('ALGORITHM')

app=FastAPI()
origins= [
     '*',
]
app.add_middleware(
     CORSMiddleware,
     allow_origins= origins,
     allow_credentials= True,
     allow_methods= ['*'],
     allow_headers= ['*']

)
if not database_exists(engine.url):
    create_database(engine.url)

Base.metadata.create_all(bind=engine)

def getdb():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close

pwd_context = CryptContext(schemes=['argon2'], deprecated="auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")
def hashPassword(password:str) -> str:
        return pwd_context.hash(password)
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(inserted_password, hashed_real_password):
     return pwd_context.verify(inserted_password, hashed_real_password)

# def get_user(db, username: str):
#     if username in db:
#         user_dict= db[username]
#         return 
# async def get_current_user(token: Annotated[str, Depends(oauth2_schema)]):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except InvalidTokenError:
#         raise credentials_exception
#     user = get_user(fake_users_db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user


#Loading hugging face model
import os
import httpx

def verify_token(token:str) ->dict:
    try:
        pyload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return pyload
    except :
        raise HTTPException(
            status_code=401,
            detail= "token not verified"
        )

def verify_user_from_token(decoded:dict, db:Session):
    try :
        user= db.query(User).filter(User.email == decoded["sub"]).first()
        return user.email
    except:
        HTTPException(
            status_code=400,
            detail= "Access denied"
        )
@app.get('/')
def testing(token: Annotated[str, Depends(oauth2_schema)], db:Session=Depends(getdb)):
    decoded = verify_token(token)
    try :
        user_email= verify_user_from_token(decoded, db)
        return {"em": user_email}
    except:
        HTTPException(
            status_code=400,
            detail= "Access denied"
        )
   

@app.post('/create_user')
def create_user(user: createUser, db:Session= Depends(getdb)):
     if db.query(User).filter(User.email == user.email).first():
         raise HTTPException(
             status_code= 404,
            detail= "user already exist"
         )
     hashed_password= hashPassword(user.password)
     print("Password received:", user.password, hashed_password, len(user.password))

     user_db= User(
         email = user.email,
         password = hashed_password,
         token = user.token
     )
     db.add(user_db)
     db.commit()
     db.refresh(user_db)
     return user_db

@app.post('/login', response_model= Token)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session=Depends(getdb)):
     user= db.query(User).filter(User.email == form_data.username).first()
     if not user or not verify_password(form_data.password, user.password):
          raise HTTPException(
               status_code=400,
               detail= "Wrong Email or Password"
          )
     access_token_expires = int(os.getenv('TOKEN_EXPIRES', 30))  # convert to int
     expires_delta = timedelta(minutes=access_token_expires)
     access_token = create_access_token(
          data= {"sub": user.email},
     )
     user.token= access_token
     db.add(user)
     db.commit()
     db.refresh(user)
     return {"access_token" : access_token, "token_type": "Bearer"}
@app.post('/predict')
def score_comment(comment:CreateComment, token: Annotated[str, Depends(oauth2_schema)], db:Session = Depends(getdb)):
     #
     decoded = verify_token(token)
     try :
        user_email= verify_user_from_token(decoded, db)
        print(user_email)
        API_URL = os.getenv('API_URL_hugging_face')
        headers = {
           "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
           }

        def query(payload):
                  response = httpx.post(API_URL, headers=headers, json=payload)
                  return response.json()

        output = query({
          "inputs": comment.comment,
          })
        print(output)
        max_score= max(output[0], key=lambda x: x['score'])['score']
        max_score_label= max(output[0], key=lambda x: x['score'])['label']
        print(max_score_label)
        avis= Avis(
           comment= comment.comment,
           score= max_score_label,
           user_id= 1)
        db.add(avis)
        db.commit()
        db.refresh(avis)
        return max_score_label
     except:
        HTTPException(
            status_code=400,
            detail= "Access denied"
        )
   
     #

   


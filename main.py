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
load_dotenv()
SECRET_KEY= os.getenv('SECRET_KEY')
ALGORITHM= os.getenv('ALGORITHM')

app=FastAPI()
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
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
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


@app.get('/')
def hello():
    API_URL = "https://router.huggingface.co/hf-inference/models/nlptown/bert-base-multilingual-uncased-sentiment"
    headers = {
    "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
     }

    def query(payload):
      response = httpx.post(API_URL, headers=headers, json=payload)
      return response.json()

    output = query({
    "inputs": "I like you. I love you",
     })
    #[{'label': '5 stars', 'score': 0.7865129113197327}, {'label': '4 stars', 'score': 0.19356273114681244}, {'label': '3 stars', 'score': 0.015475963242352009}, {'label': '2 stars', 'score': 0.0022533689625561237}, {'label': '1 star', 'score': 0.002195027656853199}]
    max_score= max(output[0], key=lambda x: x['score'])['score']


    print(max_score)
    return 'hello Nextjs'

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
          expires_delta = expires_delta
     )
     user.token= access_token
     db.add(user)
     db.commit()
     db.refresh(user)
     return {"access_token" : access_token, "token_type": "Bearer"}
@app.post('/predict')
def score_comment(comment:CreateComment, db:Session = Depends(getdb)):
     API_URL = "https://router.huggingface.co/hf-inference/models/nlptown/bert-base-multilingual-uncased-sentiment"
     headers = {
      "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
     }

     def query(payload):
      response = httpx.post(API_URL, headers=headers, json=payload)
      return response.json()

     output = query({
      "inputs": comment.comment,
     })
     max_score= max(output[0], key=lambda x: x['score'])['score']
     max_score_label= max(output[0], key=lambda x: x['score'])['label']
     avis= Avis(
           comment= comment.comment,
           score= max_score_label,
           user_id= 1)
     db.add(avis)
     db.commit()
     db.refresh(avis)
     return "done"
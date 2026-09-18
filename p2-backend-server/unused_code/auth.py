from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from Security.userdatabase import SessionLocal as UserSessionLocal
from Security.BaseModels import UserModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()

routerauth = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# The secret Key used for the JWT Token creation and validation and password hashing
SECRET_KEY = os.environ.get("SECRET_KEY")
# The Algorithm used for the JWT Token
ALGORITHM = "HS256"

argon2_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

# Base Model of a Create User Request
class CreateUserRequest(BaseModel):
    username: str
# email: str
# full_name: str      # maybe add later
    password: str

# Base Model of a Token Response
class Token(BaseModel):
    access_token: str
    token_type: str

def get_user_database():
    userDatabase = UserSessionLocal()
    try:
        yield userDatabase
    finally:
        userDatabase.close()

userdb_dependency = Annotated[Session, Depends(get_user_database)]

# Route for User Creation
@routerauth.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(dbu: userdb_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = UserModel(
        username=create_user_request.username,
        hashed_password=argon2_context.hash(create_user_request.password)
    )
    dbu.add(create_user_model)
    dbu.commit()

# Route for User Login and Token Generation
@routerauth.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 dbu: userdb_dependency):
    user = authenticate_user(dbu, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
   
    return {"access_token": token, "token_type": "bearer"}

# Function to authenticate a user
def authenticate_user(dbu, username: str, password: str):
    user = dbu.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        return False
    if not argon2_context.verify(password, user.hashed_password):
        return False
    return user

# Function to create a JWT access token
def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username,"user_id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependency to get the current user from the token
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )
        return {"username": username, "user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user",
        )


    
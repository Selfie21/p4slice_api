from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from internal.authlib import authenticate_user, get_current_active_user, get_password_hash, create_access_token
from dependencies import get_data_base
from models import User, CreateUser, Token

auth = APIRouter()

# TODO: remove in prod
db = get_data_base()
db["user1"] = User(username="user1", hashed_password=get_password_hash("pw1"), admin=True)
db["user2"] = User(username="user2", hashed_password=get_password_hash("pw2"), admin=False)
db["user3"] = User(username="user3", hashed_password=get_password_hash("pw3"), admin=False)

@auth.post("/register")
def register_user(user: CreateUser, session: dict = Depends(get_data_base)):
    if user.username in session:
        raise HTTPException(status_code=400, detail="User already registered!")

    encrypted_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=encrypted_password, admin=False)
    session[user.username] = new_user
    return {"message": "User created successfully"}


@auth.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: dict = Depends(get_data_base),
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@auth.get("/info", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user

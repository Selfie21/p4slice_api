import jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends, status
from datetime import datetime, timedelta, timezone
from typing import Optional, Annotated

from core.dependencies import get_config, get_user_data_base
from core.models import User, TokenData

config = get_config()
SECRET_KEY = config.jwt_secret_key.get_secret_value()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 45


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(bytes(password, encoding="utf-8"), bcrypt.gensalt())


def authenticate_user(database: dict, username: str, password: str) -> User:
    user = _get_user(database, username)
    if not user:
        return False
    if not _verify_password(password, user.hashed_password.get_secret_value()):
        return False
    return user


def _get_user(database, username: str) -> Optional[User]:
    if username in database:
        return database[username]


def _verify_password(plain_password, hashed_password) -> bool:
    return bcrypt.checkpw(
        bytes(plain_password, encoding="utf-8"),
        bytes(hashed_password, encoding="utf-8"),
    )


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_active_user(token: Annotated[str, Depends(oauth2_scheme)], session: dict = Depends(get_user_data_base)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception
    user = _get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def current_user_is_admin(current_user: User = Depends(get_current_active_user)):
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authorized for this action!",
            headers={"WWW-Authenticate": "Bearer"},
        )

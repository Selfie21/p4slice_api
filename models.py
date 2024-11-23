from pydantic import BaseModel, Field, SecretStr

class CreateUser(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=50)

class User(BaseModel):
    username: str = Field(max_length=50)
    hashed_password: SecretStr
    admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
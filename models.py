from pydantic import BaseModel, Field

class CreateUser(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=50)

class User(BaseModel):
    username: str = Field(max_length=50)
    hashed_password: str # TODO: input validate hex
    admin: bool
    disabled: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
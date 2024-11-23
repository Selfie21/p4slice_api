from fastapi import FastAPI

from routers.auth import auth
from routers.slice import slice

app = FastAPI()
app.include_router(auth)
app.include_router(slice)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to P4Slice your framework for creating slice instances!"
    }


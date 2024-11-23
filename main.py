from fastapi import FastAPI

from routers.auth import auth

app = FastAPI()
app.include_router(auth)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to P4Slice your framework for creating slice instances!"
    }


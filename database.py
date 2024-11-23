from models import User

user_database = {
    "user1": User(username="user1", hashed_password="password1", admin=True),
    "user2": User(username="user2", hashed_password="password2", admin=False),
    "user3": User(username="user3", hashed_password="password3", admin=False),
}
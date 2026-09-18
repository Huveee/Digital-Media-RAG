from Security.userdatabase import SessionLocal
from unused_code.UserModel import UserModel

db = SessionLocal()

users = db.query(UserModel).all()

for u in users:
    print(f"ID: {u.id}, Username: {u.username}, Hashed PW: {u.hashed_password}")

# This file is just to check all users in the database!!!
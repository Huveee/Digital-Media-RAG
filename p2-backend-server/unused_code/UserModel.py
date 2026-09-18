from Security.userdatabase import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

# Base Model of a User in the Database
"""class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    # email = Column(String, unique=True, index=True)
    # full_name = Column(String)
    # disabled = Column(Integer)  # 0 for False, 1 for True
    hashed_password = Column(String)

# relationships
    chats = relationship("Chats", back_populates="user", cascade="all, delete")"""
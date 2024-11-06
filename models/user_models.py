# models/user_models.py

from sqlalchemy import Column, Integer, String
from db.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<User {self.username}>"

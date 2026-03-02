from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.session import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(150), unique=True, nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    #  One-to-One relationship
    user_profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,  # important for 1:1
        cascade="all, delete-orphan"
    )
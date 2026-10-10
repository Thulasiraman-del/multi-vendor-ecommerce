from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String,func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    full_name:Mapped[str]=mapped_column(String(255),nullable=False)
    email:Mapped[str]=mapped_column(String(255),nullable=False,index=True,unique=True)
    password_hash:Mapped[str]=mapped_column(String(200),nullable=False)
    phone:Mapped[str|None]=mapped_column(String(20),nullable=True)
    role:Mapped[str]=mapped_column(String(50),nullable=False,default="customer")
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
    vendor=relationship("Vendor",back_populates="user",uselist=False)
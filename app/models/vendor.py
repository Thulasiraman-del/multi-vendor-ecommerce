from datetime import datetime
from sqlalchemy import (Boolean, DateTime, Integer, String, func, ForeignKey,Text)
from sqlalchemy.orm import Mapped, mapped_column,relationship
from app.models.base import Base
class Vendor(Base):
    __tablename__="vendors"
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id:Mapped[int]=mapped_column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False,unique=True)
    business_name:Mapped[str]=mapped_column(String(255),nullable=False)
    business_description:Mapped[str|None]=mapped_column(Text,nullable=True)
    is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now())
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
    user=relationship("User",back_populates="vendor")
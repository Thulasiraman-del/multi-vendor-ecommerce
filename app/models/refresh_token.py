from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    user = relationship("User")
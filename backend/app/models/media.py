import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MediaFileType
from app.database.session import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False
    )
    answer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkin_answers.id"), nullable=True
    )
    file_type: Mapped[str] = mapped_column(
        Enum(
            MediaFileType.AUDIO,
            MediaFileType.VIDEO,
            MediaFileType.COMBINED,
            name="media_file_type",
        ),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("CheckinSession", back_populates="media_files")
    answer = relationship("CheckinAnswer", back_populates="media_files")

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import QuestionCategory, SessionStatus, ProcessingStatus
from app.database.session import Base


class CheckinSession(Base):
    __tablename__ = "checkin_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.ABANDONED,
            name="session_status",
        ),
        nullable=False,
        default=SessionStatus.IN_PROGRESS,
    )
    processing_status: Mapped[str] = mapped_column(
        Enum(
            ProcessingStatus.PENDING,
            ProcessingStatus.PROCESSING,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            name="processing_status",
        ),
        nullable=False,
        default=ProcessingStatus.PENDING,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    patient = relationship("User", foreign_keys=[patient_user_id])
    answers = relationship("CheckinAnswer", back_populates="session", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="session", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="session", uselist=False)
    voice_analysis = relationship("VoiceAnalysisResult", back_populates="session", uselist=False)
    facial_analysis = relationship("FacialAnalysisResult", back_populates="session", uselist=False)
    language_analysis = relationship("LanguageAnalysisResult", back_populates="session", uselist=False)
    risk_score = relationship("RiskScore", back_populates="session", uselist=False)


class CheckinQuestion(Base):
    __tablename__ = "checkin_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    category: Mapped[str] = mapped_column(
        Enum(
            QuestionCategory.ORIENTATION,
            QuestionCategory.MEMORY_RECALL,
            QuestionCategory.LONG_TERM_MEMORY,
            QuestionCategory.EMOTIONAL_WELLBEING,
            name="question_category",
        ),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    answers = relationship("CheckinAnswer", back_populates="question")


class CheckinAnswer(Base):
    __tablename__ = "checkin_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkin_questions.id"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recording_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recording_ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response_delay_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    session = relationship("CheckinSession", back_populates="answers")
    question = relationship("CheckinQuestion", back_populates="answers")
    media_files = relationship("MediaFile", back_populates="answer")

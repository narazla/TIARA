import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False, unique=True)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="id", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CheckinSession", back_populates="transcript")


class VoiceAnalysisResult(Base):
    __tablename__ = "voice_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False, unique=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speech_rate_wpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hesitation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repetition_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pause_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_pause_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voice_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_features: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CheckinSession", back_populates="voice_analysis")


class FacialAnalysisResult(Base):
    __tablename__ = "facial_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False, unique=True)
    video_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    face_detected: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    face_detection_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_response_delay_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    facial_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_features: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CheckinSession", back_populates="facial_analysis")


class LanguageAnalysisResult(Base):
    __tablename__ = "language_analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False, unique=True)
    orientation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_recall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    coherence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vocabulary_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CheckinSession", back_populates="language_analysis")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=False, unique=True)
    patient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="risk_level"), nullable=False
    )
    voice_component: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language_component: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    facial_component: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_component: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_indicators: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CheckinSession", back_populates="risk_score")
    patient = relationship("User", foreign_keys=[patient_user_id])

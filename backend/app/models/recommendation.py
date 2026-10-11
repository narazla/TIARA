import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RecommendationCategory
from app.database.session import Base


class CareRecommendation(Base):
    __tablename__ = "care_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("checkin_sessions.id"), nullable=True)
    category: Mapped[str] = mapped_column(
        Enum(
            RecommendationCategory.COGNITIVE,
            RecommendationCategory.SOCIAL,
            RecommendationCategory.MEDICAL,
            RecommendationCategory.ROUTINE,
            RecommendationCategory.WELLBEING,
            name="recommendation_category",
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    patient = relationship("User", foreign_keys=[patient_user_id])
    session = relationship("CheckinSession", foreign_keys=[session_id])

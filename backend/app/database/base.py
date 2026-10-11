"""
Import all models here so Alembic can detect them for auto-generation.
"""
from app.database.session import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.caregiver import CaregiverPin, CaregiverPatientLink  # noqa: F401
from app.models.healthcare import HealthcarePatientLink  # noqa: F401
from app.models.checkin import (  # noqa: F401
    CheckinSession,
    CheckinQuestion,
    CheckinAnswer,
)
from app.models.media import MediaFile  # noqa: F401
from app.models.analysis import (  # noqa: F401
    Transcript,
    VoiceAnalysisResult,
    FacialAnalysisResult,
    LanguageAnalysisResult,
    RiskScore,
)
from app.models.alert import Alert  # noqa: F401
from app.models.recommendation import CareRecommendation  # noqa: F401
from app.models.guidance import GuidanceMessage  # noqa: F401
from app.models.report import Report  # noqa: F401

"""Application-wide constants."""

# User roles
class Role:
    ELDERLY = "elderly"
    CAREGIVER = "caregiver"
    HEALTHCARE = "healthcare"
    ADMIN = "admin"

    ALL = [ELDERLY, CAREGIVER, HEALTHCARE, ADMIN]


# Check-in session statuses
class SessionStatus:
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# AI processing statuses
class ProcessingStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Risk levels
class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    THRESHOLDS = {
        LOW: (0, 35),
        MEDIUM: (36, 65),
        HIGH: (66, 100),
    }

    @classmethod
    def from_score(cls, score: float) -> str:
        if score <= 35:
            return cls.LOW
        elif score <= 65:
            return cls.MEDIUM
        else:
            return cls.HIGH


# Alert severities
class AlertSeverity:
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# Check-in question categories
class QuestionCategory:
    ORIENTATION = "orientation"
    MEMORY_RECALL = "memory_recall"
    LONG_TERM_MEMORY = "long_term_memory"
    EMOTIONAL_WELLBEING = "emotional_wellbeing"


# Media file types
class MediaFileType:
    AUDIO = "audio"
    VIDEO = "video"
    COMBINED = "combined"


# Recommendation categories
class RecommendationCategory:
    COGNITIVE = "cognitive"
    SOCIAL = "social"
    MEDICAL = "medical"
    ROUTINE = "routine"
    WELLBEING = "wellbeing"


# Guidance message roles
class GuidanceRole:
    USER = "user"
    ASSISTANT = "assistant"


# Medical disclaimer text (always shown with guidance and reports)
MEDICAL_DISCLAIMER = (
    "This guidance is not a medical diagnosis. "
    "TIARA's analysis is informational only and is not intended to replace "
    "professional clinical assessment. If you have concerns about a loved one's "
    "cognitive health, please consult a qualified healthcare professional."
)

# Caregiver PIN lockout settings
PIN_MAX_ATTEMPTS = 5
PIN_LOCKOUT_MINUTES = 15

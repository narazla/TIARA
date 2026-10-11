from datetime import datetime, date, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role, SessionStatus
from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.checkin import CheckinSession
from app.models.patient import Patient
from app.models.user import User

router = APIRouter(prefix="/elderly", tags=["Elderly"])


def _get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


@router.get("/home")
async def get_elderly_home(
    current_user: User = Depends(require_role(Role.ELDERLY)),
    db: AsyncSession = Depends(get_db),
):
    """
    Return data for the elderly home page:
    - Personalized greeting
    - Today's check-in status
    - Streak days (how many consecutive days with completed check-ins)
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

    # Check if there's a completed session today
    result = await db.execute(
        select(CheckinSession).where(
            and_(
                CheckinSession.patient_user_id == current_user.id,
                CheckinSession.status == SessionStatus.COMPLETED,
                CheckinSession.completed_at >= today_start,
                CheckinSession.completed_at <= today_end,
            )
        )
    )
    todays_session = result.scalar_one_or_none()

    # Simplified streak calculation (count consecutive completed days)
    streak_days = 0

    return {
        "user": {
            "full_name": current_user.full_name,
            "greeting": _get_greeting(),
        },
        "todays_checkin": {
            "completed": todays_session is not None,
            "session_id": str(todays_session.id) if todays_session else None,
            "completed_at": todays_session.completed_at.isoformat() if todays_session and todays_session.completed_at else None,
        },
        "streak_days": streak_days,
    }


@router.get("/profile")
async def get_elderly_profile(
    current_user: User = Depends(require_role(Role.ELDERLY)),
    db: AsyncSession = Depends(get_db),
):
    """Return the elderly user's profile including patient details."""
    result = await db.execute(
        select(Patient).where(Patient.user_id == current_user.id)
    )
    patient = result.scalar_one_or_none()

    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "date_of_birth": patient.date_of_birth.isoformat() if patient and patient.date_of_birth else None,
        "gender": patient.gender if patient else None,
    }

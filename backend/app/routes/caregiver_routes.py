from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PIN_LOCKOUT_MINUTES, PIN_MAX_ATTEMPTS, Role
from app.core.dependencies import require_role
from app.core.security import create_caregiver_dashboard_token, verify_pin
from app.database.session import get_db
from app.models.caregiver import CaregiverPatientLink, CaregiverPin
from app.models.user import User
from app.services.rag_guidance_service import get_rag_answer

router = APIRouter(prefix="/caregiver", tags=["Caregiver"])


class VerifyPinRequest(BaseModel):
    pin: str


@router.post("/verify-pin")
async def verify_caregiver_pin(
    data: VerifyPinRequest,
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify the caregiver's PIN and issue a short-lived dashboard access token.
    Tracks failed attempts and enforces lockout after PIN_MAX_ATTEMPTS failures.
    """
    result = await db.execute(
        select(CaregiverPin).where(CaregiverPin.caregiver_user_id == current_user.id)
    )
    pin_record = result.scalar_one_or_none()

    if not pin_record:
        # Unified account fallback: if using the demo PIN, allow login immediately
        if data.pin == "123456":
            dashboard_token = create_caregiver_dashboard_token(str(current_user.id))
            return {
                "verified": True,
                "dashboard_token": dashboard_token,
                "expires_in": 1800,
            }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PIN configured for this caregiver",
        )

    # Check lockout
    if pin_record.locked_until and pin_record.locked_until > datetime.now(timezone.utc):
        remaining = int((pin_record.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many incorrect attempts. Try again in {remaining} minutes.",
        )

    if not verify_pin(data.pin, pin_record.hashed_pin):
        pin_record.failed_attempts += 1
        if pin_record.failed_attempts >= PIN_MAX_ATTEMPTS:
            pin_record.locked_until = datetime.now(timezone.utc) + timedelta(minutes=PIN_LOCKOUT_MINUTES)
            pin_record.failed_attempts = 0
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many incorrect attempts. Account locked for {PIN_LOCKOUT_MINUTES} minutes.",
            )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect PIN. Please try again.",
        )

    # Success — reset failed attempts and issue dashboard token
    pin_record.failed_attempts = 0
    pin_record.locked_until = None
    await db.commit()

    dashboard_token = create_caregiver_dashboard_token(str(current_user.id))
    return {
        "verified": True,
        "dashboard_token": dashboard_token,
        "expires_in": 1800,  # 30 minutes
    }


@router.get("/dashboard")
async def get_caregiver_dashboard(
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    db: AsyncSession = Depends(get_db),
):
    """
    Return caregiver dashboard analytics for the linked patient.
    Returns seed/empty data if no sessions exist yet.
    """
    from sqlalchemy import and_, desc
    from app.models.analysis import RiskScore
    from app.models.alert import Alert

    # Find linked patient
    result = await db.execute(
        select(CaregiverPatientLink).where(
            CaregiverPatientLink.caregiver_user_id == current_user.id
        ).limit(1)
    )
    link = result.scalar_one_or_none()

    patient_id = link.patient_user_id if link else current_user.id

    # Get patient user
    result = await db.execute(select(User).where(User.id == patient_id))
    patient = result.scalar_one_or_none()

    # Get recent risk scores for trend chart
    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.patient_user_id == patient_id)
        .order_by(desc(RiskScore.created_at))
        .limit(30)
    )
    risk_scores = result.scalars().all()

    trend_data = [
        {
            "date": rs.created_at.strftime("%Y-%m-%d"),
            "risk_score": round(rs.risk_score, 1),
            "risk_level": rs.risk_level,
        }
        for rs in reversed(risk_scores)
    ]

    latest_session_data = None
    if risk_scores:
        latest = risk_scores[0]
        latest_session_data = {
            "session_id": str(latest.session_id),
            "completed_at": latest.created_at.isoformat(),
            "risk_score": round(latest.risk_score, 1),
            "risk_level": latest.risk_level,
        }

    # Count unread alerts
    result = await db.execute(
        select(Alert).where(
            and_(Alert.patient_user_id == patient_id, Alert.is_read == False)
        )
    )
    unread_alerts = len(result.scalars().all())

    return {
        "patient": {
            "id": str(patient.id),
            "full_name": patient.full_name,
            "age": None,
        },
        "latest_session": latest_session_data,
        "trend_data": trend_data,
        "memory_consistency": None,
        "avg_response_delay": None,
        "speech_hesitation_rate": None,
        "unread_alerts": unread_alerts,
    }


@router.get("/alerts")
async def get_caregiver_alerts(
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    db: AsyncSession = Depends(get_db),
):
    """Return all alerts for the caregiver's linked patient."""
    from sqlalchemy import desc
    from app.models.alert import Alert

    result = await db.execute(
        select(CaregiverPatientLink).where(
            CaregiverPatientLink.caregiver_user_id == current_user.id
        ).limit(1)
    )
    link = result.scalar_one_or_none()
    patient_id = link.patient_user_id if link else current_user.id

    result = await db.execute(
        select(Alert)
        .where(Alert.patient_user_id == patient_id)
        .order_by(desc(Alert.created_at))
    )
    alerts = result.scalars().all()

    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": str(a.id),
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "suggested_action": a.suggested_action,
                "created_at": a.created_at.isoformat(),
                "is_read": a.is_read,
            }
            for a in alerts
        ],
    }


@router.get("/recommendations")
async def get_caregiver_recommendations(
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    db: AsyncSession = Depends(get_db),
):
    """Return active care recommendations for the caregiver's linked patient."""
    from sqlalchemy import desc
    from app.models.recommendation import CareRecommendation

    result = await db.execute(
        select(CaregiverPatientLink).where(
            CaregiverPatientLink.caregiver_user_id == current_user.id
        ).limit(1)
    )
    link = result.scalar_one_or_none()
    patient_id = link.patient_user_id if link else current_user.id

    result = await db.execute(
        select(CareRecommendation)
        .where(
            CareRecommendation.patient_user_id == patient_id,
            CareRecommendation.is_dismissed == False,
        )
        .order_by(desc(CareRecommendation.priority))
    )
    recs = result.scalars().all()

    def filter_by_category(cat: str):
        return [
            {"id": str(r.id), "title": r.title, "description": r.description, "priority": r.priority}
            for r in recs if r.category == cat
        ]

    return {
        "today_plan": filter_by_category("routine"),
        "cognitive_activities": filter_by_category("cognitive"),
        "social_suggestions": filter_by_category("social"),
        "medical_notes": filter_by_category("medical"),
        "when_to_seek_help": filter_by_category("wellbeing"),
    }


@router.get("/reports")
async def get_caregiver_reports(
    current_user: User = Depends(require_role(Role.CAREGIVER)),
    db: AsyncSession = Depends(get_db),
):
    """Return generated reports for the caregiver's linked patient."""
    from sqlalchemy import desc
    from app.models.report import Report

    result = await db.execute(
        select(CaregiverPatientLink).where(
            CaregiverPatientLink.caregiver_user_id == current_user.id
        ).limit(1)
    )
    link = result.scalar_one_or_none()
    patient_id = link.patient_user_id if link else current_user.id

    result = await db.execute(
        select(Report)
        .where(Report.patient_user_id == patient_id)
        .order_by(desc(Report.created_at))
    )
    reports = result.scalars().all()

    return {
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "report_month": r.report_month.isoformat(),
                "checkin_count": r.checkin_count,
                "avg_risk_score": r.avg_risk_score,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ]
    }

class GuidanceAskRequest(BaseModel):
    question: str


@router.post("/guidance/ask")
async def ask_guidance_ai(
    data: GuidanceAskRequest,
    current_user: User = Depends(require_role(Role.CAREGIVER)),
):
    """
    Ask the Dementia Guidance AI (RAG-based chatbot) a question.
    Answers are grounded in validated medical documents (PNPK Demensia, Kemenkes caregiver guides).
    """
    if not data.question or not data.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    try:
        answer = get_rag_answer(data.question)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Guidance AI is temporarily unavailable: {str(e)}",
        )

    return {
        "question": data.question,
        "answer": answer,
    }

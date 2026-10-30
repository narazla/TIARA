import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
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

logger = logging.getLogger(__name__)

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN belum dikonfigurasi untuk caregiver ini",
        )

    # Check lockout
    if pin_record.locked_until and pin_record.locked_until > datetime.now(timezone.utc):
        remaining = int((pin_record.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Terlalu banyak percobaan salah. Coba lagi dalam {remaining} menit.",
        )

    if not verify_pin(data.pin, pin_record.hashed_pin):
        pin_record.failed_attempts += 1
        if pin_record.failed_attempts >= PIN_MAX_ATTEMPTS:
            pin_record.locked_until = datetime.now(timezone.utc) + timedelta(minutes=PIN_LOCKOUT_MINUTES)
            pin_record.failed_attempts = 0
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Terlalu banyak percobaan salah. Akun dikunci selama {PIN_LOCKOUT_MINUTES} menit.",
            )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN salah. Silakan coba lagi.",
        )

    # Success: reset failed attempts and issue dashboard token
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
    Metrics are computed from the last 7 days vs the preceding 7 days.
    Returns null for metrics when no analysis data exists.
    """
    from statistics import mean
    from sqlalchemy import and_, desc
    from app.core.config import settings as app_settings
    from app.models.analysis import (
        FacialAnalysisResult,
        LanguageAnalysisResult,
        RiskScore,
        VoiceAnalysisResult,
    )
    from app.models.alert import Alert
    from app.models.checkin import CheckinSession

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
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data pasien tidak ditemukan",
        )

    # ── Risk score trend (last 30 days) ────────────────────────
    now_utc = datetime.now(timezone.utc)
    result = await db.execute(
        select(RiskScore)
        .where(
            RiskScore.patient_user_id == patient_id,
            RiskScore.created_at >= now_utc - timedelta(days=30),
        )
        .order_by(desc(RiskScore.created_at))
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

    # ── Time windows for 7-day metrics ─────────────────────────
    week_ago = now_utc - timedelta(days=7)
    two_weeks_ago = now_utc - timedelta(days=14)

    # Helper: get completed session IDs for a time window
    async def _session_ids_in_window(start: datetime, end: datetime) -> list:
        r = await db.execute(
            select(CheckinSession.id).where(
                and_(
                    CheckinSession.patient_user_id == patient_id,
                    CheckinSession.completed_at >= start,
                    CheckinSession.completed_at < end,
                )
            )
        )
        return [row[0] for row in r.all()]

    cur_ids = await _session_ids_in_window(week_ago, now_utc)
    prev_ids = await _session_ids_in_window(two_weeks_ago, week_ago)

    # ── memory_consistency: mean(memory_recall_score) × 100 ────
    # Source: LanguageAnalysisResult.memory_recall_score (0-1 float)
    async def _memory_consistency(session_ids: list) -> float | None:
        if not session_ids:
            return None
        r = await db.execute(
            select(LanguageAnalysisResult.memory_recall_score).where(
                and_(
                    LanguageAnalysisResult.session_id.in_(session_ids),
                    LanguageAnalysisResult.memory_recall_score.is_not(None),
                )
            )
        )
        vals = [row[0] for row in r.all() if row[0] is not None]
        return round(mean(vals) * 100, 1) if vals else None

    # ── avg_response_delay: mean(avg_response_delay_seconds) ───
    # Source: FacialAnalysisResult.avg_response_delay_seconds (float, seconds)
    async def _avg_response_delay(session_ids: list) -> float | None:
        if not session_ids:
            return None
        r = await db.execute(
            select(FacialAnalysisResult.avg_response_delay_seconds).where(
                and_(
                    FacialAnalysisResult.session_id.in_(session_ids),
                    FacialAnalysisResult.avg_response_delay_seconds.is_not(None),
                )
            )
        )
        vals = [row[0] for row in r.all() if row[0] is not None]
        return round(mean(vals), 2) if vals else None

    # ── speech_hesitation_rate: mean(hesitation_count / duration × 60) ──
    # Source: VoiceAnalysisResult.hesitation_count, .duration_seconds
    async def _speech_hesitation_rate(session_ids: list) -> float | None:
        if not session_ids:
            return None
        r = await db.execute(
            select(
                VoiceAnalysisResult.hesitation_count,
                VoiceAnalysisResult.duration_seconds,
            ).where(
                and_(
                    VoiceAnalysisResult.session_id.in_(session_ids),
                    VoiceAnalysisResult.duration_seconds.is_not(None),
                    VoiceAnalysisResult.duration_seconds > 0,
                )
            )
        )
        rates = [
            (row[0] / row[1]) * 60
            for row in r.all()
            if row[0] is not None and row[1] and row[1] > 0
        ]
        return round(mean(rates), 2) if rates else None

    mem_cur = await _memory_consistency(cur_ids)
    mem_prev = await _memory_consistency(prev_ids)
    delay_cur = await _avg_response_delay(cur_ids)
    delay_prev = await _avg_response_delay(prev_ids)
    hes_cur = await _speech_hesitation_rate(cur_ids)
    hes_prev = await _speech_hesitation_rate(prev_ids)

    def _delta(cur: float | None, prev: float | None) -> float | None:
        if cur is None or prev is None:
            return None
        return round(cur - prev, 2)

    # ── Unread alerts ───────────────────────────────────────────
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
        "memory_consistency": mem_cur,
        "memory_consistency_delta": _delta(mem_cur, mem_prev),
        "avg_response_delay": delay_cur,
        "avg_response_delay_delta": _delta(delay_cur, delay_prev),
        "speech_hesitation_rate": hes_cur,
        "speech_hesitation_rate_delta": _delta(hes_cur, hes_prev),
        "unread_alerts": unread_alerts,
        "is_simulated": app_settings.DEMO_MODE,
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
            detail="Pertanyaan tidak boleh kosong",
        )

    try:
        result = await run_in_threadpool(get_rag_answer, data.question)
    except Exception as e:
        logger.error("Guidance AI error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan Panduan AI sedang tidak tersedia. Silakan coba lagi.",
        )

    return {
        "question": data.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }
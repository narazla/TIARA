"""
Route untuk tenaga kesehatan.

- GET /healthcare/patients                         daftar pasien yang terhubung dengan akun dokter
- GET /healthcare/patients/{patient_user_id}/summary   ringkasan longitudinal per pasien

Perhitungan indikator mengikuti dashboard caregiver (7 hari terakhir vs 7 hari sebelumnya).
Semua angka adalah indikator informatif, bukan diagnosis.
"""
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.constants import Role
from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.alert import Alert
from app.models.analysis import (
    FacialAnalysisResult,
    LanguageAnalysisResult,
    RiskScore,
    VoiceAnalysisResult,
)
from app.models.checkin import CheckinSession
from app.models.healthcare import HealthcarePatientLink
from app.models.patient import Patient
from app.models.report import Report
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/healthcare", tags=["Healthcare"])

HARI_PERHATIAN_TANPA_CHECKIN = 3


# ── Fungsi bantu ───────────────────────────────────────────────
def _umur(tanggal_lahir: Optional[date]) -> Optional[int]:
    if not tanggal_lahir:
        return None
    hari_ini = date.today()
    sudah_ulang_tahun = (hari_ini.month, hari_ini.day) >= (tanggal_lahir.month, tanggal_lahir.day)
    return hari_ini.year - tanggal_lahir.year - (0 if sudah_ulang_tahun else 1)


def _selisih(sekarang: Optional[float], sebelumnya: Optional[float]) -> Optional[float]:
    if sekarang is None or sebelumnya is None:
        return None
    return round(sekarang - sebelumnya, 2)


async def _pasien_terhubung(db: AsyncSession, hcw_user_id: uuid.UUID) -> list[tuple[User, Optional[Patient]]]:
    hasil = await db.execute(
        select(User, Patient)
        .select_from(User)
        .join(HealthcarePatientLink, HealthcarePatientLink.patient_user_id == User.id)
        .outerjoin(Patient, Patient.user_id == User.id)
        .where(HealthcarePatientLink.hcw_user_id == hcw_user_id)
    )
    return [(baris[0], baris[1]) for baris in hasil.all()]


async def _id_sesi(db: AsyncSession, patient_user_id: uuid.UUID, mulai: datetime, akhir: datetime) -> list:
    hasil = await db.execute(
        select(CheckinSession.id).where(
            and_(
                CheckinSession.patient_user_id == patient_user_id,
                CheckinSession.completed_at >= mulai,
                CheckinSession.completed_at < akhir,
            )
        )
    )
    return [baris[0] for baris in hasil.all()]


async def _konsistensi_memori(db: AsyncSession, id_sesi: list) -> Optional[float]:
    if not id_sesi:
        return None
    hasil = await db.execute(
        select(LanguageAnalysisResult.memory_recall_score).where(
            and_(
                LanguageAnalysisResult.session_id.in_(id_sesi),
                LanguageAnalysisResult.memory_recall_score.is_not(None),
            )
        )
    )
    nilai = [baris[0] for baris in hasil.all() if baris[0] is not None]
    return round(mean(nilai) * 100, 1) if nilai else None


async def _jeda_respons(db: AsyncSession, id_sesi: list) -> Optional[float]:
    if not id_sesi:
        return None
    hasil = await db.execute(
        select(FacialAnalysisResult.avg_response_delay_seconds).where(
            and_(
                FacialAnalysisResult.session_id.in_(id_sesi),
                FacialAnalysisResult.avg_response_delay_seconds.is_not(None),
            )
        )
    )
    nilai = [baris[0] for baris in hasil.all() if baris[0] is not None]
    return round(mean(nilai), 2) if nilai else None


async def _keraguan_bicara(db: AsyncSession, id_sesi: list) -> Optional[float]:
    if not id_sesi:
        return None
    hasil = await db.execute(
        select(
            VoiceAnalysisResult.hesitation_count,
            VoiceAnalysisResult.duration_seconds,
        ).where(
            and_(
                VoiceAnalysisResult.session_id.in_(id_sesi),
                VoiceAnalysisResult.duration_seconds.is_not(None),
                VoiceAnalysisResult.duration_seconds > 0,
            )
        )
    )
    laju = [
        (baris[0] / baris[1]) * 60
        for baris in hasil.all()
        if baris[0] is not None and baris[1] and baris[1] > 0
    ]
    return round(mean(laju), 2) if laju else None


async def _skor_terbaru(db: AsyncSession, patient_user_id: uuid.UUID) -> Optional[RiskScore]:
    hasil = await db.execute(
        select(RiskScore)
        .where(RiskScore.patient_user_id == patient_user_id)
        .order_by(desc(RiskScore.created_at))
        .limit(1)
    )
    return hasil.scalar_one_or_none()


async def _checkin_terakhir(db: AsyncSession, patient_user_id: uuid.UUID) -> Optional[datetime]:
    hasil = await db.execute(
        select(func.max(CheckinSession.completed_at)).where(
            CheckinSession.patient_user_id == patient_user_id
        )
    )
    return hasil.scalar_one_or_none()


async def _jumlah_peringatan_belum_dibaca(db: AsyncSession, patient_user_id: uuid.UUID) -> int:
    hasil = await db.execute(
        select(func.count())
        .select_from(Alert)
        .where(and_(Alert.patient_user_id == patient_user_id, Alert.is_read == False))  # noqa: E712
    )
    return int(hasil.scalar_one() or 0)


def _hari_sejak(waktu: Optional[datetime], sekarang: datetime) -> Optional[int]:
    if waktu is None:
        return None
    return max(0, (sekarang.date() - waktu.date()).days)


# ── Endpoint ───────────────────────────────────────────────────
@router.get("/patients")
async def daftar_pasien(
    current_user: User = Depends(require_role(Role.HEALTHCARE)),
    db: AsyncSession = Depends(get_db),
):
    """Daftar pasien terhubung, diurutkan dari yang paling perlu perhatian."""
    sekarang = datetime.now(timezone.utc)
    kartu = []

    for pasien_user, profil in await _pasien_terhubung(db, current_user.id):
        terbaru = await _skor_terbaru(db, pasien_user.id)
        terakhir = await _checkin_terakhir(db, pasien_user.id)
        hari = _hari_sejak(terakhir, sekarang)
        tingkat = terbaru.risk_level if terbaru else None
        perlu_perhatian = tingkat == "high" or (
            hari is not None and hari >= HARI_PERHATIAN_TANPA_CHECKIN
        )
        kartu.append(
            {
                "id": str(pasien_user.id),
                "full_name": pasien_user.full_name,
                "age": _umur(profil.date_of_birth) if profil else None,
                "latest_risk_score": round(terbaru.risk_score, 1) if terbaru else None,
                "latest_risk_level": tingkat,
                "last_checkin_at": terakhir.isoformat() if terakhir else None,
                "days_since_last_checkin": hari,
                "unread_alerts": await _jumlah_peringatan_belum_dibaca(db, pasien_user.id),
                "needs_attention": perlu_perhatian,
            }
        )

    kartu.sort(
        key=lambda k: (
            0 if k["needs_attention"] else 1,
            -(k["latest_risk_score"] if k["latest_risk_score"] is not None else -1),
        )
    )

    return {
        "total": len(kartu),
        "patients": kartu,
        "is_simulated": app_settings.DEMO_MODE,
    }


@router.get("/patients/{patient_user_id}/summary")
async def ringkasan_pasien(
    patient_user_id: uuid.UUID,
    current_user: User = Depends(require_role(Role.HEALTHCARE)),
    db: AsyncSession = Depends(get_db),
):
    """Ringkasan longitudinal satu pasien. Hanya untuk pasien yang terhubung dengan dokter ini."""
    hasil = await db.execute(
        select(HealthcarePatientLink).where(
            and_(
                HealthcarePatientLink.hcw_user_id == current_user.id,
                HealthcarePatientLink.patient_user_id == patient_user_id,
            )
        )
    )
    if hasil.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pasien tidak terhubung dengan akun Anda",
        )

    hasil = await db.execute(select(User).where(User.id == patient_user_id))
    pasien_user = hasil.scalar_one_or_none()
    if not pasien_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data pasien tidak ditemukan",
        )

    hasil = await db.execute(select(Patient).where(Patient.user_id == patient_user_id))
    profil = hasil.scalar_one_or_none()

    sekarang = datetime.now(timezone.utc)

    # Tren skor 30 hari
    hasil = await db.execute(
        select(RiskScore)
        .where(
            RiskScore.patient_user_id == patient_user_id,
            RiskScore.created_at >= sekarang - timedelta(days=30),
        )
        .order_by(desc(RiskScore.created_at))
    )
    skor_30_hari = hasil.scalars().all()

    tren = [
        {
            "date": rs.created_at.strftime("%Y-%m-%d"),
            "risk_score": round(rs.risk_score, 1),
            "risk_level": rs.risk_level,
        }
        for rs in reversed(skor_30_hari)
    ]

    sesi_terbaru = None
    if skor_30_hari:
        terbaru = skor_30_hari[0]
        sesi_terbaru = {
            "session_id": str(terbaru.session_id),
            "completed_at": terbaru.created_at.isoformat(),
            "risk_score": round(terbaru.risk_score, 1),
            "risk_level": terbaru.risk_level,
        }

    # Indikator 7 hari vs 7 hari sebelumnya
    seminggu_lalu = sekarang - timedelta(days=7)
    dua_minggu_lalu = sekarang - timedelta(days=14)
    sesi_ini = await _id_sesi(db, patient_user_id, seminggu_lalu, sekarang)
    sesi_lalu = await _id_sesi(db, patient_user_id, dua_minggu_lalu, seminggu_lalu)

    memori_ini = await _konsistensi_memori(db, sesi_ini)
    memori_lalu = await _konsistensi_memori(db, sesi_lalu)
    jeda_ini = await _jeda_respons(db, sesi_ini)
    jeda_lalu = await _jeda_respons(db, sesi_lalu)
    ragu_ini = await _keraguan_bicara(db, sesi_ini)
    ragu_lalu = await _keraguan_bicara(db, sesi_lalu)

    # Jumlah check-in 30 hari dan check-in terakhir
    sesi_30_hari = await _id_sesi(db, patient_user_id, sekarang - timedelta(days=30), sekarang)
    terakhir = await _checkin_terakhir(db, patient_user_id)

    # Peringatan dan laporan
    hasil = await db.execute(
        select(Alert)
        .where(Alert.patient_user_id == patient_user_id)
        .order_by(desc(Alert.created_at))
    )
    peringatan = hasil.scalars().all()

    hasil = await db.execute(
        select(Report)
        .where(Report.patient_user_id == patient_user_id)
        .order_by(desc(Report.created_at))
    )
    laporan = hasil.scalars().all()

    return {
        "patient": {
            "id": str(pasien_user.id),
            "full_name": pasien_user.full_name,
            "age": _umur(profil.date_of_birth) if profil else None,
            "gender": profil.gender if profil else None,
        },
        "latest_session": sesi_terbaru,
        "trend_data": tren,
        "memory_consistency": memori_ini,
        "memory_consistency_delta": _selisih(memori_ini, memori_lalu),
        "avg_response_delay": jeda_ini,
        "avg_response_delay_delta": _selisih(jeda_ini, jeda_lalu),
        "speech_hesitation_rate": ragu_ini,
        "speech_hesitation_rate_delta": _selisih(ragu_ini, ragu_lalu),
        "checkin_count_30d": len(sesi_30_hari),
        "days_since_last_checkin": _hari_sejak(terakhir, sekarang),
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
            for a in peringatan
        ],
        "reports": [
            {
                "id": str(r.id),
                "title": r.title,
                "report_month": r.report_month.isoformat(),
                "checkin_count": r.checkin_count,
                "avg_risk_score": r.avg_risk_score,
                "content_json": r.content_json,
                "created_at": r.created_at.isoformat(),
            }
            for r in laporan
        ],
        "is_simulated": app_settings.DEMO_MODE,
    }

"""
TIARA Seed Script
=================
Membuat akun demo dan data awal untuk pengembangan dan demo lomba.

Demo credentials:
    Elderly:     elderly@tiara.app / password123
    Caregiver:   caregiver@tiara.app / password123 / PIN: 123456
    Healthcare:  doctor@tiara.app / password123

Run with:
    cd backend
    python -m app.scripts.seed                 # seed biasa (idempoten)
    python -m app.scripts.seed --reset-demo    # buat ulang riwayat simulasi pasien demo

Riwayat simulasi hanya dibuat jika DEMO_MODE=true. Data simulasi ditandai dengan
provider "simulasi-demo" pada tabel facial_analysis_results.
"""
import argparse
import asyncio
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from statistics import mean

# Ensure backend/ is on the path when running as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Import base FIRST: this registers all ORM models so SQLAlchemy can
# resolve string-based relationship() references (e.g. "MediaFile").
import app.database.base  # noqa: F401

from app.core.config import settings
from app.core.constants import (
    AlertSeverity,
    ProcessingStatus,
    QuestionCategory,
    RecommendationCategory,
    Role,
    SessionStatus,
)
from app.core.security import hash_password, hash_pin
from app.database.session import AsyncSessionLocal
from app.models.alert import Alert
from app.models.analysis import (
    FacialAnalysisResult,
    LanguageAnalysisResult,
    RiskScore,
    VoiceAnalysisResult,
)
from app.models.caregiver import CaregiverPatientLink, CaregiverPin
from app.models.checkin import CheckinQuestion, CheckinSession
from app.models.healthcare import HealthcarePatientLink
from app.models.patient import Patient
from app.models.recommendation import CareRecommendation
from app.models.report import Report
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEMO_QUESTIONS = [
    # Orientasi
    {"category": QuestionCategory.ORIENTATION, "question_text": "Hari apa sekarang, Bapak/Ibu?", "order_index": 0},
    {"category": QuestionCategory.ORIENTATION, "question_text": "Apakah Bapak/Ibu tahu sedang berada di mana sekarang?", "order_index": 1},
    # Daya Ingat
    {"category": QuestionCategory.MEMORY_RECALL, "question_text": "Tadi pagi Bapak/Ibu makan apa?", "order_index": 2},
    {"category": QuestionCategory.MEMORY_RECALL, "question_text": "Apakah ada yang berkunjung kemarin?", "order_index": 3},
    # Memori Jangka Panjang
    {"category": QuestionCategory.LONG_TERM_MEMORY, "question_text": "Ceritakan tentang pekerjaan pertama Bapak/Ibu.", "order_index": 4},
    {"category": QuestionCategory.LONG_TERM_MEMORY, "question_text": "Ceritakan satu kenangan masa kecil yang Bapak/Ibu sukai.", "order_index": 5},
    # Kesejahteraan Emosional
    {"category": QuestionCategory.EMOTIONAL_WELLBEING, "question_text": "Bagaimana perasaan Bapak/Ibu hari ini?", "order_index": 6},
    {"category": QuestionCategory.EMOTIONAL_WELLBEING, "question_text": "Apa yang membuat Bapak/Ibu senang belakangan ini?", "order_index": 7},
]

# ── Pengaturan riwayat simulasi ────────────────────────────────
DEMO_PROVIDER = "simulasi-demo"
JUMLAH_HARI = 60
HARI_TERLEWAT = {44, 20, 9, 8}  # 9 dan 8 berurutan, sesuai peringatan "terlewat 2 hari"
BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

DEMO_RECOMMENDATIONS = [
    (RecommendationCategory.ROUTINE, "Jaga jadwal tidur dan bangun yang sama",
     "Mulai tidur dan bangun pada jam yang sama setiap hari, dan hindari tidur siang lebih dari 30 menit.", 3),
    (RecommendationCategory.ROUTINE, "Siapkan jadwal harian sederhana",
     "Tempel jadwal harian dengan tulisan besar di tempat yang mudah dilihat untuk membantu orientasi waktu.", 2),
    (RecommendationCategory.COGNITIVE, "Dengarkan musik kesukaan bersama",
     "Luangkan waktu mendengarkan lagu yang disukai. Terapi musik tercatat membantu fungsi kognitif pada pasien demensia (PNPK Demensia hal 121).", 3),
    (RecommendationCategory.COGNITIVE, "Lakukan kegiatan yang menjadi hobinya",
     "Ajak melakukan kegiatan yang dulu disukai atau hal baru yang menyenangkan, sesuai kemampuan pada hari itu.", 2),
    (RecommendationCategory.SOCIAL, "Jaga kontak sosial yang hangat",
     "Ajak keluarga atau tetangga berkunjung sebentar, atau lakukan panggilan video agar lansia tetap merasa terhubung.", 3),
    (RecommendationCategory.SOCIAL, "Ajak bercerita tentang kenangan",
     "Mintalah lansia menceritakan satu kenangan yang disukai, lalu dengarkan dengan sabar tanpa mengoreksi.", 2),
    (RecommendationCategory.MEDICAL, "Catat perubahan untuk dibawa ke dokter",
     "Catat perubahan tidur, nafsu makan, dan perilaku selama beberapa hari. Catatan ini membantu dokter saat kontrol.", 3),
    (RecommendationCategory.MEDICAL, "Pastikan lingkungan rumah aman",
     "Periksa lantai tidak licin, pencahayaan cukup, dan pegangan tersedia untuk mencegah jatuh.", 2),
    (RecommendationCategory.WELLBEING, "Konsultasikan bila perubahan terjadi cepat",
     "Hubungi tenaga kesehatan bila perubahan perilaku atau daya ingat terlihat mendadak atau memburuk dengan cepat.", 3),
    (RecommendationCategory.WELLBEING, "Jadwalkan kontrol berkala",
     "Buat jadwal kontrol rutin dengan dokter dan bawa catatan serta ringkasan dari TIARA.", 2),
]


async def seed_questions(db: AsyncSession) -> None:
    """Upsert pertanyaan check-in berdasarkan order_index (idempoten)."""
    for q_data in DEMO_QUESTIONS:
        result = await db.execute(
            select(CheckinQuestion).where(CheckinQuestion.order_index == q_data["order_index"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.question_text = q_data["question_text"]
            existing.category = q_data["category"]
            logger.info(f"Diperbarui pertanyaan order_index={q_data['order_index']}")
        else:
            db.add(CheckinQuestion(**q_data))
            logger.info(f"Ditambahkan pertanyaan order_index={q_data['order_index']}")

    logger.info(f"Sinkronisasi {len(DEMO_QUESTIONS)} pertanyaan check-in selesai")


def _batas(nilai: float, bawah: float = 0.0, atas: float = 1.0) -> float:
    return max(bawah, min(atas, nilai))


def _level_risiko(skor: float) -> str:
    if skor >= 7:
        return "high"
    if skor >= 4:
        return "medium"
    return "low"


async def _hapus_data_demo(db: AsyncSession, patient_user_id: uuid.UUID, session_ids: list) -> None:
    """Hapus hanya data simulasi milik pasien demo. Tidak menyentuh users, PIN, atau tabel link."""
    await db.execute(delete(Alert).where(Alert.patient_user_id == patient_user_id))
    await db.execute(delete(CareRecommendation).where(CareRecommendation.patient_user_id == patient_user_id))
    await db.execute(delete(Report).where(Report.patient_user_id == patient_user_id))
    if session_ids:
        for model in (RiskScore, LanguageAnalysisResult, VoiceAnalysisResult, FacialAnalysisResult):
            await db.execute(delete(model).where(model.session_id.in_(session_ids)))
        await db.execute(delete(CheckinSession).where(CheckinSession.id.in_(session_ids)))
    await db.flush()


async def seed_demo_history(db: AsyncSession, patient_user_id: uuid.UUID, reset: bool = False) -> None:
    """Buat riwayat simulasi 60 hari untuk pasien demo (idempoten, deterministik)."""
    if not settings.DEMO_MODE:
        logger.info("DEMO_MODE=false: riwayat simulasi dilewati")
        return

    result = await db.execute(
        select(FacialAnalysisResult.session_id)
        .join(CheckinSession, CheckinSession.id == FacialAnalysisResult.session_id)
        .where(
            CheckinSession.patient_user_id == patient_user_id,
            FacialAnalysisResult.provider == DEMO_PROVIDER,
        )
    )
    sesi_demo = [row[0] for row in result.all()]

    if sesi_demo and not reset:
        logger.info(
            "Riwayat simulasi sudah ada (%d sesi), dilewati. Gunakan --reset-demo untuk membuat ulang.",
            len(sesi_demo),
        )
        return

    if reset:
        await _hapus_data_demo(db, patient_user_id, sesi_demo)
        logger.info("Data simulasi lama dihapus (%d sesi)", len(sesi_demo))

    # Tandai profil pasien sudah memiliki baseline
    hasil = await db.execute(select(Patient).where(Patient.user_id == patient_user_id))
    pasien = hasil.scalar_one_or_none()
    if pasien:
        pasien.baseline_established = True

    rng = random.Random(42)
    sekarang = datetime.now(timezone.utc)
    info_sesi: list[tuple[datetime, float]] = []

    for hari_lalu in range(JUMLAH_HARI - 1, -1, -1):
        if hari_lalu in HARI_TERLEWAT:
            continue

        selesai = sekarang.replace(hour=2, minute=0, second=0, microsecond=0) - timedelta(days=hari_lalu)
        if selesai > sekarang:
            selesai = sekarang - timedelta(minutes=5)

        durasi = rng.uniform(150, 240)
        mulai = selesai - timedelta(seconds=durasi + 30)

        # drift: 0 sebelum 10 hari terakhir, naik sampai 1 pada hari ini
        drift = max(0.0, (10 - hari_lalu) / 10)
        lambat = (JUMLAH_HARI - 1 - hari_lalu) / (JUMLAH_HARI - 1)

        skor = _batas(2.4 + 0.4 * lambat + 2.0 * drift + rng.uniform(-0.25, 0.25), 0.0, 10.0)
        level = _level_risiko(skor)

        memori = _batas(0.88 - 0.12 * drift + rng.uniform(-0.02, 0.02))
        jeda = max(0.5, 2.0 + 1.4 * drift + rng.uniform(-0.15, 0.15))
        laju_ragu = max(0.2, 1.4 + 1.8 * drift + rng.uniform(-0.15, 0.15))
        wpm = 112 - 15 * drift + rng.uniform(-3, 3)
        jumlah_ragu = max(0, round(laju_ragu * durasi / 60))

        sesi_id = uuid.uuid4()
        db.add(CheckinSession(
            id=sesi_id,
            patient_user_id=patient_user_id,
            status=SessionStatus.COMPLETED,
            processing_status=ProcessingStatus.COMPLETED,
            started_at=mulai,
            completed_at=selesai,
            question_count=4,
            answer_count=4,
            total_duration_seconds=round(durasi + 30, 1),
            consent_given=True,
            consent_at=mulai,
            created_at=selesai,
        ))
        db.add(VoiceAnalysisResult(
            session_id=sesi_id,
            duration_seconds=round(durasi, 1),
            speech_rate_wpm=round(wpm, 1),
            hesitation_count=jumlah_ragu,
            repetition_count=rng.randint(0, 1 + round(2 * drift)),
            pause_count=rng.randint(6, 10) + round(4 * drift),
            avg_pause_duration=round(0.8 + 0.5 * drift + rng.uniform(-0.05, 0.05), 2),
            voice_risk_score=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            created_at=selesai,
        ))
        db.add(LanguageAnalysisResult(
            session_id=sesi_id,
            orientation_score=round(_batas(0.92 - 0.06 * drift + rng.uniform(-0.02, 0.02)), 2),
            memory_recall_score=round(memori, 2),
            coherence_score=round(_batas(0.88 - 0.05 * drift + rng.uniform(-0.02, 0.02)), 2),
            vocabulary_score=round(_batas(0.85 - 0.02 * drift + rng.uniform(-0.02, 0.02)), 2),
            emotional_tone=rng.choice(["positif", "netral", "netral"]),
            language_risk_score=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            created_at=selesai,
        ))
        db.add(FacialAnalysisResult(
            session_id=sesi_id,
            video_duration_seconds=round(durasi, 1),
            face_detected=True,
            face_detection_confidence=round(rng.uniform(0.9, 0.98), 2),
            avg_response_delay_seconds=round(jeda, 2),
            facial_risk_score=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            provider=DEMO_PROVIDER,
            created_at=selesai,
        ))

        if level == "low":
            ringkasan = "Sesi simulasi: indikator berada dalam kisaran biasa."
            indikator: list[str] = []
        else:
            ringkasan = "Sesi simulasi: beberapa indikator sedikit berubah dibanding pekan sebelumnya."
            indikator = [
                "Jeda respons lebih panjang dari pekan sebelumnya",
                "Skor daya ingat sedikit lebih rendah dari biasanya",
            ]
        db.add(RiskScore(
            session_id=sesi_id,
            patient_user_id=patient_user_id,
            risk_score=round(skor, 1),
            risk_level=level,
            voice_component=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            language_component=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            facial_component=round(_batas(skor + rng.uniform(-0.5, 0.5), 0, 10), 1),
            memory_component=round(_batas((1 - memori) * 10 + 1.5, 0, 10), 1),
            summary=ringkasan,
            main_indicators=indikator,
            created_at=selesai,
        ))
        info_sesi.append((selesai, skor))

    # ── Peringatan ─────────────────────────────────────────────
    db.add_all([
        Alert(
            patient_user_id=patient_user_id,
            severity=AlertSeverity.WARNING,
            title="Jeda respons meningkat dalam 10 hari terakhir",
            description=(
                "Rata-rata jeda respons pada check-in sepuluh hari terakhir lebih panjang "
                "dibanding sebelumnya. Ini indikator informatif, bukan diagnosis."
            ),
            suggested_action=(
                "Perhatikan apakah ada perubahan tidur, kelelahan, atau perubahan obat dari dokter, "
                "lalu catat untuk dibahas pada kontrol berikutnya. Jika perubahan terasa cepat, "
                "konsultasikan dengan tenaga kesehatan."
            ),
            is_read=False,
            created_at=sekarang - timedelta(days=1),
        ),
        Alert(
            patient_user_id=patient_user_id,
            severity=AlertSeverity.INFO,
            title="Check-in terlewat 2 hari berturut-turut",
            description="Tidak ada check-in pada dua hari berturut-turut pekan lalu.",
            suggested_action="Ajak lansia melakukan check-in pada waktu yang sama setiap hari, misalnya setelah sarapan.",
            is_read=False,
            created_at=sekarang - timedelta(days=7),
        ),
    ])

    # ── Rekomendasi ────────────────────────────────────────────
    for kategori, judul, deskripsi, prioritas in DEMO_RECOMMENDATIONS:
        db.add(CareRecommendation(
            patient_user_id=patient_user_id,
            category=kategori,
            title=judul,
            description=deskripsi,
            priority=prioritas,
            is_dismissed=False,
        ))

    # ── Laporan bulanan (dihitung dari data sesi di atas) ──────
    per_bulan: dict[tuple[int, int], list[float]] = {}
    for selesai, skor in info_sesi:
        per_bulan.setdefault((selesai.year, selesai.month), []).append(skor)

    for (tahun, bulan), daftar_skor in sorted(per_bulan.items())[-2:]:
        bulan_depan = (tahun + 1, 1) if bulan == 12 else (tahun, bulan + 1)
        dibuat = min(
            datetime(bulan_depan[0], bulan_depan[1], 1, 1, 0, tzinfo=timezone.utc),
            sekarang,
        )
        db.add(Report(
            patient_user_id=patient_user_id,
            report_month=datetime(tahun, bulan, 1).date(),
            title=f"Laporan Bulanan {BULAN[bulan - 1]} {tahun}",
            content_json={"catatan": "Data simulasi untuk demo"},
            checkin_count=len(daftar_skor),
            avg_risk_score=round(mean(daftar_skor), 1),
            created_at=dibuat,
        ))

    await db.flush()
    logger.info(
        "Riwayat simulasi dibuat: %d sesi, 2 peringatan, %d rekomendasi, %d laporan",
        len(info_sesi),
        len(DEMO_RECOMMENDATIONS),
        min(2, len(per_bulan)),
    )


async def get_or_create_user(db: AsyncSession, email: str, **kwargs) -> tuple[User, bool]:
    """Return an existing user by email, or create a new one."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        return user, False

    user = User(email=email, **kwargs)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user, True


async def seed(db: AsyncSession, reset_demo: bool = False) -> None:
    logger.info("Starting TIARA seed...")

    # ── Elderly user ───────────────────────────────────────────
    elderly, created = await get_or_create_user(
        db,
        email="elderly@tiara.app",
        hashed_password=hash_password("password123"),
        full_name="Nenek Ladya",
        role=Role.ELDERLY,
    )
    if created:
        logger.info("Created elderly user: elderly@tiara.app")

    # Patient profile for elderly user
    result = await db.execute(select(Patient).where(Patient.user_id == elderly.id))
    if not result.scalar_one_or_none():
        patient = Patient(user_id=elderly.id, gender="F")
        db.add(patient)
        logger.info("Created patient profile for Nenek Ladya")

    # ── Caregiver user ─────────────────────────────────────────
    caregiver, created = await get_or_create_user(
        db,
        email="caregiver@tiara.app",
        hashed_password=hash_password("password123"),
        full_name="Nazla",
        role=Role.CAREGIVER,
    )
    if created:
        logger.info("Created caregiver user: caregiver@tiara.app")

    # Caregiver PIN (123456)
    result = await db.execute(
        select(CaregiverPin).where(CaregiverPin.caregiver_user_id == caregiver.id)
    )
    if not result.scalar_one_or_none():
        pin = CaregiverPin(
            caregiver_user_id=caregiver.id,
            hashed_pin=hash_pin("123456"),
        )
        db.add(pin)
        logger.info("Created caregiver PIN (123456) for Nazla")

    # Caregiver-patient link
    result = await db.execute(
        select(CaregiverPatientLink).where(
            CaregiverPatientLink.caregiver_user_id == caregiver.id,
            CaregiverPatientLink.patient_user_id == elderly.id,
        )
    )
    if not result.scalar_one_or_none():
        link = CaregiverPatientLink(
            caregiver_user_id=caregiver.id,
            patient_user_id=elderly.id,
            relationship_type="daughter",
            is_primary=True,
        )
        db.add(link)
        logger.info("Linked caregiver Nazla -> Nenek Ladya")

    # ── Healthcare worker ──────────────────────────────────────
    hcw, created = await get_or_create_user(
        db,
        email="doctor@tiara.app",
        hashed_password=hash_password("password123"),
        full_name="Dr. Sarah",
        role=Role.HEALTHCARE,
    )
    if created:
        logger.info("Created healthcare worker: doctor@tiara.app")

    # Healthcare-patient link
    result = await db.execute(
        select(HealthcarePatientLink).where(
            HealthcarePatientLink.hcw_user_id == hcw.id,
            HealthcarePatientLink.patient_user_id == elderly.id,
        )
    )
    if not result.scalar_one_or_none():
        hcw_link = HealthcarePatientLink(
            hcw_user_id=hcw.id,
            patient_user_id=elderly.id,
            specialty="Geriatrics",
        )
        db.add(hcw_link)
        logger.info("Linked Dr. Sarah -> Nenek Ladya")

    # ── Question bank ──────────────────────────────────────────
    await seed_questions(db)

    # ── Riwayat simulasi untuk dashboard demo ──────────────────
    await seed_demo_history(db, elderly.id, reset=reset_demo)

    await db.commit()
    logger.info("Seed selesai.")
    logger.info("")
    logger.info("Demo credentials:")
    logger.info("  Elderly:    elderly@tiara.app / password123")
    logger.info("  Caregiver:  caregiver@tiara.app / password123 / PIN: 123456")
    logger.info("  Healthcare: doctor@tiara.app / password123")


async def main(reset_demo: bool = False):
    async with AsyncSessionLocal() as db:
        try:
            await seed(db, reset_demo=reset_demo)
        except Exception as e:
            await db.rollback()
            logger.error(f"Seed failed: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed data demo TIARA")
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="Hapus dan buat ulang riwayat simulasi pasien demo",
    )
    args = parser.parse_args()
    asyncio.run(main(reset_demo=args.reset_demo))
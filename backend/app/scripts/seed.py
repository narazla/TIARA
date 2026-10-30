"""
TIARA Seed Script
=================
Creates demo users and initial data for development and competition demos.

Demo credentials:
    Elderly:     elderly@tiara.app / password123
    Caregiver:   caregiver@tiara.app / password123 / PIN: 123456
    Healthcare:  doctor@tiara.app / password123

Run with:
    cd backend
    python -m app.scripts.seed
"""
import asyncio
import logging
import sys
import os

# Ensure backend/ is on the path when running as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import base FIRST — this registers all ORM models so SQLAlchemy can
# resolve string-based relationship() references (e.g. "MediaFile").
import app.database.base  # noqa: F401

from app.core.constants import QuestionCategory, Role
from app.core.security import hash_password, hash_pin
from app.database.session import AsyncSessionLocal
from app.models.caregiver import CaregiverPatientLink, CaregiverPin
from app.models.checkin import CheckinQuestion
from app.models.healthcare import HealthcarePatientLink
from app.models.patient import Patient
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


async def seed(db: AsyncSession) -> None:
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
        logger.info("Linked caregiver Nazla → Nenek Ladya")

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
        logger.info("Linked Dr. Sarah → Nenek Ladya")

    # ── Question bank ──────────────────────────────────────────
    await seed_questions(db)

    await db.commit()
    logger.info("✅ Seed completed successfully!")
    logger.info("")
    logger.info("Demo credentials:")
    logger.info("  Elderly:    elderly@tiara.app / password123")
    logger.info("  Caregiver:  caregiver@tiara.app / password123 / PIN: 123456")
    logger.info("  Healthcare: doctor@tiara.app / password123")


async def main():
    async with AsyncSessionLocal() as db:
        try:
            await seed(db)
        except Exception as e:
            await db.rollback()
            logger.error(f"Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

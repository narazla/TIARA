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
    # Orientation
    {"category": QuestionCategory.ORIENTATION, "question_text": "What day is today?", "order_index": 0},
    {"category": QuestionCategory.ORIENTATION, "question_text": "Do you know where you are right now?", "order_index": 1},
    # Memory Recall
    {"category": QuestionCategory.MEMORY_RECALL, "question_text": "What did you eat this morning?", "order_index": 2},
    {"category": QuestionCategory.MEMORY_RECALL, "question_text": "Did anyone visit you yesterday?", "order_index": 3},
    # Long-Term Memory
    {"category": QuestionCategory.LONG_TERM_MEMORY, "question_text": "Tell me about your first job.", "order_index": 4},
    {"category": QuestionCategory.LONG_TERM_MEMORY, "question_text": "What is one childhood memory you remember fondly?", "order_index": 5},
    # Emotional Wellbeing
    {"category": QuestionCategory.EMOTIONAL_WELLBEING, "question_text": "How are you feeling today?", "order_index": 6},
    {"category": QuestionCategory.EMOTIONAL_WELLBEING, "question_text": "What made you happy recently?", "order_index": 7},
]


async def seed_questions(db: AsyncSession) -> None:
    """Seed the question bank if not already present."""
    result = await db.execute(select(CheckinQuestion).limit(1))
    if result.scalar_one_or_none():
        logger.info("Questions already seeded, skipping...")
        return

    for q_data in DEMO_QUESTIONS:
        question = CheckinQuestion(**q_data)
        db.add(question)

    logger.info(f"Seeded {len(DEMO_QUESTIONS)} check-in questions")


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

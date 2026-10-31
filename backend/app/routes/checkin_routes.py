"""
Rute check-in suara lansia.

Alur: start -> kirim jawaban per pertanyaan (audio) -> finish.
Saat finish, audio ditranskripsi dengan faster-whisper, fitur pola bicara dihitung,
lalu hasilnya disimpan ke transcripts, voice_analysis_results, dan risk_scores.
Komponen wajah dan bahasa tidak diisi karena belum ada pipeline-nya.
"""
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.constants import AlertSeverity, MediaFileType, ProcessingStatus, Role, SessionStatus
from app.core.dependencies import require_role
from app.database.session import get_db
from app.models.alert import Alert
from app.models.analysis import RiskScore, Transcript, VoiceAnalysisResult
from app.models.checkin import CheckinAnswer, CheckinQuestion, CheckinSession
from app.models.media import MediaFile
from app.models.user import User
from app.services import media_crypto
from app.services import voice_analysis_service as suara

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/elderly/checkin", tags=["Check-in"])

JUMLAH_PERTANYAAN = 4
MAKS_UKURAN_BYTE = 15 * 1024 * 1024
MIN_UKURAN_BYTE = 1000
JUMLAH_RIWAYAT_PEMBANDING = 14


class MulaiRequest(BaseModel):
    consent: bool


async def _sesi_milik_pengguna(db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID) -> CheckinSession:
    hasil = await db.execute(
        select(CheckinSession).where(
            CheckinSession.id == session_id,
            CheckinSession.patient_user_id == user_id,
        )
    )
    sesi = hasil.scalar_one_or_none()
    if not sesi:
        raise HTTPException(status_code=404, detail="Sesi check-in tidak ditemukan")
    return sesi


@router.post("/start", status_code=201)
async def mulai_sesi(
    data: MulaiRequest,
    current_user: User = Depends(require_role(Role.ELDERLY)),
    db: AsyncSession = Depends(get_db),
):
    """Mulai sesi check-in baru. Wajib ada persetujuan merekam suara."""
    if not data.consent:
        raise HTTPException(status_code=400, detail="Persetujuan merekam suara diperlukan")

    # Sesi lama yang tidak selesai ditandai ditinggalkan
    await db.execute(
        update(CheckinSession)
        .where(
            CheckinSession.patient_user_id == current_user.id,
            CheckinSession.status == SessionStatus.IN_PROGRESS,
        )
        .values(status=SessionStatus.ABANDONED)
    )

    sekarang = datetime.now(timezone.utc)
    sesi = CheckinSession(
        patient_user_id=current_user.id,
        status=SessionStatus.IN_PROGRESS,
        processing_status=ProcessingStatus.PENDING,
        started_at=sekarang,
        question_count=JUMLAH_PERTANYAAN,
        consent_given=True,
        consent_at=sekarang,
    )
    db.add(sesi)
    await db.commit()
    await db.refresh(sesi)
    return {"session_id": str(sesi.id)}


@router.post("/{session_id}/answer", status_code=201)
async def kirim_jawaban(
    session_id: uuid.UUID,
    question_order: int = Form(...),
    audio: UploadFile = File(...),
    current_user: User = Depends(require_role(Role.ELDERLY)),
    db: AsyncSession = Depends(get_db),
):
    """Simpan rekaman jawaban untuk satu pertanyaan (order_index pertanyaan di tabel)."""
    sesi = await _sesi_milik_pengguna(db, session_id, current_user.id)
    if sesi.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Sesi check-in sudah ditutup")

    hasil = await db.execute(
        select(CheckinQuestion).where(
            CheckinQuestion.order_index == question_order,
            CheckinQuestion.is_active.is_(True),
        )
    )
    pertanyaan = hasil.scalar_one_or_none()
    if not pertanyaan:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan")

    isi = await audio.read()
    if len(isi) < MIN_UKURAN_BYTE:
        raise HTTPException(status_code=400, detail="Rekaman terlalu pendek")
    if len(isi) > MAKS_UKURAN_BYTE:
        raise HTTPException(status_code=413, detail="Rekaman terlalu besar")

    # Jawaban ulang untuk pertanyaan yang sama menggantikan yang lama
    hasil = await db.execute(
        select(CheckinAnswer).where(
            CheckinAnswer.session_id == sesi.id,
            CheckinAnswer.question_id == pertanyaan.id,
        )
    )
    for lama in hasil.scalars().all():
        await db.execute(delete(MediaFile).where(MediaFile.answer_id == lama.id))
        await db.delete(lama)
    await db.flush()

    folder = Path(settings.MEDIA_STORAGE_PATH) / str(sesi.id)
    folder.mkdir(parents=True, exist_ok=True)
    try:
        terenkripsi = media_crypto.enkripsi(isi)
    except media_crypto.KunciTidakAda:
        logger.error("MEDIA_ENCRYPTION_KEY belum diatur, rekaman tidak disimpan")
        raise HTTPException(status_code=503, detail="Penyimpanan rekaman belum dikonfigurasi")
    jalur = folder / f"jawaban_{question_order}.webm.enc"
    jalur.write_bytes(terenkripsi)

    jawaban = CheckinAnswer(
        session_id=sesi.id,
        question_id=pertanyaan.id,
        question_text=pertanyaan.question_text,
        category=str(pertanyaan.category),
        recording_ended_at=datetime.now(timezone.utc),
    )
    db.add(jawaban)
    await db.flush()
    jawaban_id = jawaban.id
    db.add(
        MediaFile(
            session_id=sesi.id,
            answer_id=jawaban_id,
            file_type=MediaFileType.AUDIO,
            file_path=str(jalur),
            file_size_bytes=len(isi),
            mime_type=audio.content_type,
        )
    )
    await db.commit()
    return {"answer_id": str(jawaban_id)}


async def _riwayat_pribadi(db: AsyncSession, patient_user_id: uuid.UUID, session_id: uuid.UUID) -> list:
    """Hasil analisis suara nyata sebelumnya milik lansia ini (data simulasi tidak ikut)."""
    hasil = await db.execute(
        select(VoiceAnalysisResult)
        .join(CheckinSession, CheckinSession.id == VoiceAnalysisResult.session_id)
        .where(
            CheckinSession.patient_user_id == patient_user_id,
            CheckinSession.id != session_id,
            VoiceAnalysisResult.raw_features["sumber"].astext == suara.SUMBER,
        )
        .order_by(VoiceAnalysisResult.created_at.desc())
        .limit(JUMLAH_RIWAYAT_PEMBANDING)
    )
    riwayat = []
    for baris in hasil.scalars().all():
        fitur = baris.raw_features or {}
        riwayat.append({
            "wpm": baris.speech_rate_wpm,
            "jeda_rata_rata": baris.avg_pause_duration,
            "ragu_per_menit": fitur.get("ragu_per_menit"),
            "jeda_respons": fitur.get("jeda_respons"),
        })
    return riwayat


async def _tandai_gagal(db: AsyncSession, session_id: uuid.UUID, ditinggalkan: bool = False) -> None:
    await db.rollback()
    nilai = {"processing_status": ProcessingStatus.FAILED}
    if ditinggalkan:
        nilai["status"] = SessionStatus.ABANDONED
    await db.execute(update(CheckinSession).where(CheckinSession.id == session_id).values(**nilai))
    await db.commit()


async def _tambah_peringatan(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    session_id: uuid.UUID,
    severity: str,
    title: str,
    description: str,
    suggested_action: str,
) -> bool:
    """Tambah alert untuk caregiver. Satu judul yang sama hanya sekali dalam 12 jam."""
    batas = datetime.now(timezone.utc) - timedelta(hours=12)
    ada = await db.execute(
        select(Alert.id).where(
            Alert.patient_user_id == patient_user_id,
            Alert.title == title,
            Alert.created_at >= batas,
        ).limit(1)
    )
    if ada.first() is not None:
        return False
    db.add(Alert(
        patient_user_id=patient_user_id,
        session_id=session_id,
        severity=severity,
        title=title,
        description=description,
        suggested_action=suggested_action,
        is_read=False,
    ))
    return True


async def _peringatan_tanpa_suara(db: AsyncSession, patient_user_id: uuid.UUID, session_id: uuid.UUID) -> None:
    if await _tambah_peringatan(
        db, patient_user_id, session_id, AlertSeverity.INFO,
        "Check-in hari ini tidak terekam",
        "Tidak ada suara yang cukup terdeteksi pada check-in terakhir, sehingga skor tidak dapat dihitung.",
        "Periksa mikrofon, lalu ajak lansia mengulang check-in di ruangan yang tenang.",
    ):
        await db.commit()


@router.post("/{session_id}/finish")
async def selesai(
    session_id: uuid.UUID,
    current_user: User = Depends(require_role(Role.ELDERLY)),
    db: AsyncSession = Depends(get_db),
):
    """Proses semua rekaman sesi ini dan simpan hasil analisis suara."""
    sesi = await _sesi_milik_pengguna(db, session_id, current_user.id)
    if sesi.processing_status == ProcessingStatus.COMPLETED:
        return {"status": "selesai", "session_id": str(sesi.id)}
    if sesi.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Sesi sedang diproses")

    patient_user_id = sesi.patient_user_id
    mulai = sesi.started_at
    sesi.processing_status = ProcessingStatus.PROCESSING
    await db.commit()

    try:
        hasil = await db.execute(
            select(CheckinAnswer)
            .where(CheckinAnswer.session_id == session_id)
            .order_by(CheckinAnswer.created_at)
        )
        daftar_jawaban = hasil.scalars().all()
        hasil = await db.execute(
            select(MediaFile).where(
                MediaFile.session_id == session_id,
                MediaFile.file_type == MediaFileType.AUDIO,
            )
        )
        media = {m.answer_id: m for m in hasil.scalars().all()}

        potongan = []
        for jawaban in daftar_jawaban:
            berkas = media.get(jawaban.id)
            if not berkas:
                continue
            sumber = io.BytesIO(media_crypto.baca_rekaman(berkas.file_path))
            potongan.append((jawaban, await run_in_threadpool(suara.transkripsi, sumber)))

        fitur_per_jawaban = [suara.fitur_jawaban(t["words"]) for _, t in potongan]
        durasi_total = sum(t["duration"] for _, t in potongan)
        gabungan = suara.gabung_fitur(fitur_per_jawaban, durasi_total)

        if gabungan["jumlah_kata"] < suara.MIN_KATA_SESI:
            await _tandai_gagal(db, session_id, ditinggalkan=True)
            await _peringatan_tanpa_suara(db, patient_user_id, session_id)
            return {"status": "tidak_ada_suara", "session_id": str(session_id)}

        riwayat = await _riwayat_pribadi(db, patient_user_id, session_id)
        dasar, dari_riwayat = suara.tentukan_dasar(riwayat)
        penilaian = suara.hitung_skor(gabungan, dasar)
        if penilaian["skor"] is None:
            await _tandai_gagal(db, session_id, ditinggalkan=True)
            await _peringatan_tanpa_suara(db, patient_user_id, session_id)
            return {"status": "tidak_ada_suara", "session_id": str(session_id)}

        for (jawaban, t), fitur in zip(potongan, fitur_per_jawaban):
            jawaban.answer_text = t["text"]
            jawaban.response_delay_seconds = fitur["jeda_respons"]

        peluang = [t["confidence"] for _, t in potongan if t["confidence"] is not None]
        db.add(Transcript(
            session_id=session_id,
            transcript_text="\n".join(t["text"] for _, t in potongan if t["text"]),
            word_count=gabungan["jumlah_kata"],
            provider=f"faster-whisper-{settings.WHISPER_MODEL_SIZE}",
            confidence=(sum(peluang) / len(peluang)) if peluang else None,
            language="id",
        ))
        db.add(VoiceAnalysisResult(
            session_id=session_id,
            duration_seconds=round(durasi_total, 1),
            speech_rate_wpm=round(gabungan["wpm"], 1) if gabungan["wpm"] is not None else None,
            hesitation_count=gabungan["jumlah_ragu"],
            repetition_count=gabungan["jumlah_ulang"],
            pause_count=gabungan["jumlah_jeda"],
            avg_pause_duration=round(gabungan["jeda_rata_rata"], 2),
            avg_response_delay_seconds=round(gabungan["jeda_respons"], 2) if gabungan["jeda_respons"] is not None else None,
            voice_risk_score=penilaian["skor"],
            raw_features={
                "sumber": suara.SUMBER,
                "model": settings.WHISPER_MODEL_SIZE,
                "pembanding": "riwayat pribadi" if dari_riwayat else "nilai acuan umum",
                "jumlah_riwayat": len(riwayat),
                "ragu_per_menit": gabungan["ragu_per_menit"],
                "jeda_respons": gabungan["jeda_respons"],
                "komponen": penilaian["komponen"],
            },
        ))
        asal = (
            f"riwayat pribadi ({len(riwayat)} sesi sebelumnya)"
            if dari_riwayat
            else "nilai acuan umum karena riwayat pribadi belum cukup"
        )
        db.add(RiskScore(
            session_id=session_id,
            patient_user_id=patient_user_id,
            risk_score=penilaian["skor"],
            risk_level=penilaian["tingkat"],
            voice_component=penilaian["skor"],
            language_component=None,
            facial_component=None,
            memory_component=None,
            summary=(
                f"Skor dihitung dari pola bicara pada sesi ini dan dibandingkan dengan {asal}. "
                "Ini indikator informatif, bukan diagnosis."
            ),
            main_indicators=penilaian["indikator"],
        ))

        perlu_perhatian = False
        if penilaian["tingkat"] == "high":
            alasan = "; ".join(penilaian["indikator"]) or "pola bicara menyimpang dari pembanding"
            perlu_perhatian = await _tambah_peringatan(
                db, patient_user_id, session_id, AlertSeverity.WARNING,
                "Pola bicara hari ini menyimpang dari biasanya",
                f"Skor risiko hari ini {penilaian['skor']} (Tinggi), dibandingkan dengan {asal}. "
                f"Penyebab utama: {alasan}. Ini indikator informatif, bukan diagnosis.",
                "Tanyakan kabar lansia, perhatikan tidur, kelelahan dan perubahan obat, lalu catat untuk "
                "dibahas dengan tenaga kesehatan. Jika perubahan terasa cepat, segera konsultasikan.",
            )

        selesai_pada = datetime.now(timezone.utc)
        sesi.status = SessionStatus.COMPLETED
        sesi.processing_status = ProcessingStatus.COMPLETED
        sesi.completed_at = selesai_pada
        sesi.answer_count = len(daftar_jawaban)
        sesi.total_duration_seconds = round((selesai_pada - mulai).total_seconds(), 1)
        await db.commit()
    except ImportError:
        logger.exception("faster-whisper tidak terpasang")
        await _tandai_gagal(db, session_id)
        raise HTTPException(status_code=503, detail="Layanan transkripsi belum tersedia")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Gagal memproses check-in %s", session_id)
        await _tandai_gagal(db, session_id)
        raise HTTPException(status_code=500, detail="Check-in belum bisa diproses")

    return {"status": "selesai", "session_id": str(session_id), "perlu_perhatian": perlu_perhatian}

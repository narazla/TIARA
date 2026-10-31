"""
Generator rekomendasi perawatan BERBASIS ATURAN (bukan AI).

Dipanggil setelah satu sesi check-in selesai dan skornya tersimpan.
Memilih teks dari tingkat skor dan tren sederhana. Tanpa LLM, tanpa jaringan.

Penanda: rekomendasi buatan sistem memiliki session_id terisi. Rekomendasi
seed memiliki session_id kosong dan tidak pernah disentuh di sini.
Hanya satu set buatan sistem per pasien yang disimpan (yang terbaru).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rekomendasi_templates import (
    PRIORITAS,
    TEMPLAT,
    TEMPLAT_TREN_NAIK,
)
from app.models.analysis import RiskScore
from app.models.recommendation import CareRecommendation

AMBANG_TREN = 1.0  # selisih skor yang dianggap naik atau turun


def normalisasi_level(tingkat: Optional[str]) -> Optional[str]:
    """Ubah 'high/medium/low' atau 'Tinggi/Sedang/Rendah' ke rendah/sedang/tinggi."""
    if not tingkat:
        return None
    peta = {
        "high": "tinggi", "tinggi": "tinggi",
        "medium": "sedang", "sedang": "sedang",
        "low": "rendah", "rendah": "rendah",
    }
    return peta.get(str(tingkat).strip().lower())


def hitung_tren(skor: float, skor_sebelumnya: list[float]) -> Optional[str]:
    """Kembalikan 'naik', 'turun', 'stabil', atau None jika tidak ada pembanding."""
    if not skor_sebelumnya:
        return None
    selisih = skor - mean(skor_sebelumnya)
    if selisih >= AMBANG_TREN:
        return "naik"
    if selisih <= -AMBANG_TREN:
        return "turun"
    return "stabil"


def pilih_rekomendasi(level: Optional[str], tren: Optional[str]) -> list[tuple]:
    """Murni: kembalikan daftar (kategori, judul, deskripsi, prioritas)."""
    if level not in TEMPLAT:
        return []
    butir = list(TEMPLAT[level])
    if tren == "naik" and level != "tinggi":
        butir.append(TEMPLAT_TREN_NAIK)
    return [(k, j, d, PRIORITAS.get(k, 0)) for (k, j, d) in butir]


async def _skor_sepekan(
    db: AsyncSession, patient_user_id: uuid.UUID, session_id: uuid.UUID
) -> list[float]:
    batas = datetime.now(timezone.utc) - timedelta(days=7)
    hasil = await db.execute(
        select(RiskScore.risk_score).where(
            RiskScore.patient_user_id == patient_user_id,
            RiskScore.session_id != session_id,
            RiskScore.created_at >= batas,
        )
    )
    return [baris[0] for baris in hasil.all() if baris[0] is not None]


async def buat_rekomendasi_sesi(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    session_id: uuid.UUID,
    tingkat: Optional[str],
    skor: Optional[float],
) -> int:
    """
    Ganti set rekomendasi buatan sistem milik pasien dengan set baru dari sesi ini.
    Kembalikan jumlah butir yang dibuat. Tidak melakukan commit.
    """
    level = normalisasi_level(tingkat)
    if level is None or skor is None:
        return 0

    tren = hitung_tren(float(skor), await _skor_sepekan(db, patient_user_id, session_id))
    daftar = pilih_rekomendasi(level, tren)
    if not daftar:
        return 0

    # Hapus hanya rekomendasi buatan sistem (session_id terisi). Seed tidak disentuh.
    await db.execute(
        delete(CareRecommendation).where(
            CareRecommendation.patient_user_id == patient_user_id,
            CareRecommendation.session_id.is_not(None),
        )
    )
    for kategori, judul, deskripsi, prioritas in daftar:
        db.add(CareRecommendation(
            patient_user_id=patient_user_id,
            session_id=session_id,
            category=kategori,
            title=judul,
            description=deskripsi,
            priority=prioritas,
            is_dismissed=False,
        ))
    return len(daftar)

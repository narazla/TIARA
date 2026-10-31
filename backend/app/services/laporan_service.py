"""
Layanan generator laporan bulanan TIARA.

Membuat atau memperbarui (upsert) satu laporan per pasien per bulan
dari data sesi dan skor risiko nyata pada bulan tersebut.

Catatan: skor hanya berasal dari komponen suara. Laporan ini adalah
indikator informatif dan bukan diagnosis. Keputusan klinis tetap pada
tenaga kesehatan.
"""
from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, datetime, timezone
from statistics import mean
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.analysis import RiskScore
from app.models.checkin import CheckinSession
from app.models.report import Report

BULAN_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

CATATAN_TETAP = (
    "Laporan ini adalah indikator informatif dan bukan diagnosis. "
    "Keputusan klinis tetap pada tenaga kesehatan."
)


def _level_label(level: str) -> str:
    """Konversi nilai risk_level (high/medium/low atau Tinggi/Sedang/Rendah) ke label Indonesia."""
    mapping = {
        "high": "Tinggi", "medium": "Sedang", "low": "Rendah",
        "tinggi": "Tinggi", "sedang": "Sedang", "rendah": "Rendah",
    }
    return mapping.get(level.lower(), level)


def _normalisasi_level(level: str) -> str:
    """
    Normalisasi nilai risk_level ke salah satu dari tiga kunci baku: 'high', 'medium', 'low'.
    Menerima nilai bahasa Inggris (high/medium/low) maupun bahasa Indonesia
    (Tinggi/Sedang/Rendah), huruf besar kecil tidak berpengaruh.
    Nilai yang tidak dikenal dikembalikan apa adanya.
    """
    mapping = {
        "high": "high", "medium": "medium", "low": "low",
        "tinggi": "high", "sedang": "medium", "rendah": "low",
    }
    return mapping.get(level.lower(), level.lower())


def _hitung_sebaran(daftar_rs: list) -> dict[str, int]:
    """
    Hitung sebaran level dari daftar RiskScore.
    Mengembalikan dict dengan kunci 'high', 'medium', 'low'.
    """
    sebaran: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for rs in daftar_rs:
        kunci = _normalisasi_level(rs.risk_level)
        sebaran[kunci] = sebaran.get(kunci, 0) + 1
    return sebaran


def _level_dominan(sebaran: dict[str, int]) -> list[str]:
    """
    Kembalikan daftar kunci level dengan jumlah tertinggi.
    Jika dua atau lebih level seri, kembalikan keduanya.
    Mengembalikan daftar kosong jika semua nol.
    """
    if not any(sebaran.values()):
        return []
    maks = max(sebaran.values())
    return [k for k, v in sebaran.items() if v == maks]


def _buat_ringkasan(
    jumlah_sesi: int,
    jumlah_tanpa_suara: int,
    avg_skor: Optional[float],
    skor_tertinggi: Optional[float],
    skor_terendah: Optional[float],
    sebaran: dict[str, int],
    perbandingan_teks: str,
    jumlah_peringatan: int,
) -> str:
    """
    Buat paragraf ringkasan dari angka-angka laporan menggunakan template kalimat.
    Tidak menggunakan LLM.
    """
    tanpa_suara_teks = (
        f", {jumlah_tanpa_suara} di antaranya tidak memiliki data suara"
        if jumlah_tanpa_suara
        else ""
    )

    if avg_skor is None:
        # Tidak ada skor sama sekali
        baris = (
            f"Pada bulan ini terdapat {jumlah_sesi} sesi check-in{tanpa_suara_teks}, "
            "tetapi tidak ada yang memiliki data suara yang dapat dinilai. "
            "Skor Risiko Kognitif tidak dapat dihitung. "
            f"{perbandingan_teks} "
            f"Terdapat {jumlah_peringatan} peringatan pada bulan ini."
        )
        return baris.strip()

    # Ada skor: hitung level dominan
    dominan = _level_dominan(sebaran)
    if not dominan:
        dominan_teks = ""
    elif len(dominan) == 1:
        k = dominan[0]
        dominan_teks = (
            f"Level yang paling sering muncul adalah {_level_label(k)} "
            f"({sebaran[k]} sesi). "
        )
    else:
        bagian = " dan ".join(
            f"{_level_label(k)} ({sebaran[k]} sesi)" for k in dominan
        )
        dominan_teks = f"Level yang paling sering muncul adalah {bagian} (seri). "

    baris = (
        f"Pada bulan ini terdapat {jumlah_sesi} sesi check-in{tanpa_suara_teks}. "
        f"Rata-rata Skor Risiko Kognitif adalah {avg_skor:.1f} "
        f"(tertinggi {skor_tertinggi:.1f}, terendah {skor_terendah:.1f}). "
        f"{dominan_teks}"
        f"{perbandingan_teks} "
        f"Terdapat {jumlah_peringatan} peringatan pada bulan ini."
    )
    return baris.strip()


async def buat_atau_perbarui_laporan(
    db: AsyncSession,
    patient_user_id: uuid.UUID,
    tahun: int,
    bulan: int,
    generated_by_user_id: Optional[uuid.UUID] = None,
) -> dict:
    """
    Buat atau perbarui (upsert) laporan bulanan untuk satu pasien.

    Kembalikan dict dengan kunci 'laporan' (objek Report) dan 'dibuat_baru' (bool).
    Kembalikan dict dengan kunci 'pesan' jika bulan tidak memiliki sesi.
    """
    # Tentukan rentang tanggal bulan
    hari_terakhir = monthrange(tahun, bulan)[1]
    awal_bulan = datetime(tahun, bulan, 1, 0, 0, 0, tzinfo=timezone.utc)
    akhir_bulan = datetime(tahun, bulan, hari_terakhir, 23, 59, 59, 999999, tzinfo=timezone.utc)

    # Ambil semua sesi pada bulan tersebut
    hasil_sesi = await db.execute(
        select(CheckinSession.id).where(
            and_(
                CheckinSession.patient_user_id == patient_user_id,
                CheckinSession.completed_at >= awal_bulan,
                CheckinSession.completed_at <= akhir_bulan,
            )
        )
    )
    id_sesi = [baris[0] for baris in hasil_sesi.all()]
    jumlah_sesi = len(id_sesi)

    if jumlah_sesi == 0:
        return {"pesan": f"Tidak ada sesi check-in pada {BULAN_ID[bulan - 1]} {tahun}. Laporan tidak dibuat."}

    # Ambil RiskScore untuk sesi-sesi tersebut
    hasil_rs = await db.execute(
        select(RiskScore).where(
            and_(
                RiskScore.patient_user_id == patient_user_id,
                RiskScore.session_id.in_(id_sesi),
            )
        )
    )
    daftar_rs = hasil_rs.scalars().all()
    id_sesi_dengan_skor = {rs.session_id for rs in daftar_rs}
    jumlah_tanpa_suara = jumlah_sesi - len(id_sesi_dengan_skor)

    daftar_skor = [rs.risk_score for rs in daftar_rs]

    if daftar_skor:
        avg_skor: Optional[float] = round(mean(daftar_skor), 1)
        skor_tertinggi: Optional[float] = round(max(daftar_skor), 1)
        skor_terendah: Optional[float] = round(min(daftar_skor), 1)
        sebaran = _hitung_sebaran(daftar_rs)
    else:
        avg_skor = None
        skor_tertinggi = None
        skor_terendah = None
        sebaran = {"high": 0, "medium": 0, "low": 0}

    # Perbandingan dengan bulan sebelumnya
    if bulan == 1:
        tahun_lalu, bulan_lalu = tahun - 1, 12
    else:
        tahun_lalu, bulan_lalu = tahun, bulan - 1

    hari_terakhir_lalu = monthrange(tahun_lalu, bulan_lalu)[1]
    awal_lalu = datetime(tahun_lalu, bulan_lalu, 1, 0, 0, 0, tzinfo=timezone.utc)
    akhir_lalu = datetime(tahun_lalu, bulan_lalu, hari_terakhir_lalu, 23, 59, 59, 999999, tzinfo=timezone.utc)

    hasil_lalu = await db.execute(
        select(RiskScore.risk_score).where(
            and_(
                RiskScore.patient_user_id == patient_user_id,
                RiskScore.created_at >= awal_lalu,
                RiskScore.created_at <= akhir_lalu,
            )
        )
    )
    skor_lalu = [baris[0] for baris in hasil_lalu.all()]
    if skor_lalu and avg_skor is not None:
        avg_lalu = round(mean(skor_lalu), 1)
        selisih = round(avg_skor - avg_lalu, 1)
        arah = "naik" if selisih > 0 else ("turun" if selisih < 0 else "sama")
        perbandingan_teks = (
            f"Dibanding {BULAN_ID[bulan_lalu - 1]} {tahun_lalu} (rata-rata {avg_lalu:.1f}), "
            f"rata-rata skor bulan ini {arah} sebesar {abs(selisih):.1f}."
        )
    else:
        perbandingan_teks = "Belum ada pembanding dari bulan sebelumnya."

    # Jumlah peringatan pada bulan tersebut
    hasil_alert = await db.execute(
        select(func.count()).select_from(Alert).where(
            and_(
                Alert.patient_user_id == patient_user_id,
                Alert.created_at >= awal_bulan,
                Alert.created_at <= akhir_bulan,
            )
        )
    )
    jumlah_peringatan = int(hasil_alert.scalar_one() or 0)

    ringkasan = _buat_ringkasan(
        jumlah_sesi=jumlah_sesi,
        jumlah_tanpa_suara=jumlah_tanpa_suara,
        avg_skor=avg_skor,
        skor_tertinggi=skor_tertinggi,
        skor_terendah=skor_terendah,
        sebaran=sebaran,
        perbandingan_teks=perbandingan_teks,
        jumlah_peringatan=jumlah_peringatan,
    )

    content_json = {
        "jumlah_sesi": jumlah_sesi,
        "jumlah_tanpa_suara": jumlah_tanpa_suara,
        "avg_skor_risiko": avg_skor,
        "skor_tertinggi": skor_tertinggi,
        "skor_terendah": skor_terendah,
        "sebaran_level": {
            "Tinggi": sebaran["high"],
            "Sedang": sebaran["medium"],
            "Rendah": sebaran["low"],
        },
        "perbandingan_bulan_lalu": perbandingan_teks,
        "jumlah_peringatan": jumlah_peringatan,
        "ringkasan": ringkasan,
        "catatan_tetap": CATATAN_TETAP,
    }

    report_month_date = date(tahun, bulan, 1)
    title = f"Laporan Bulanan {BULAN_ID[bulan - 1]} {tahun}"

    # Upsert: cari laporan yang sudah ada untuk bulan ini
    hasil_existing = await db.execute(
        select(Report).where(
            and_(
                Report.patient_user_id == patient_user_id,
                Report.report_month == report_month_date,
            )
        )
    )
    existing = hasil_existing.scalar_one_or_none()

    if existing:
        existing.title = title
        existing.content_json = content_json
        existing.checkin_count = jumlah_sesi
        existing.avg_risk_score = avg_skor
        existing.generated_by_user_id = generated_by_user_id
        await db.commit()
        await db.refresh(existing)
        return {"laporan": existing, "dibuat_baru": False}
    else:
        laporan_baru = Report(
            patient_user_id=patient_user_id,
            generated_by_user_id=generated_by_user_id,
            report_month=report_month_date,
            title=title,
            content_json=content_json,
            checkin_count=jumlah_sesi,
            avg_risk_score=avg_skor,
        )
        db.add(laporan_baru)
        await db.commit()
        await db.refresh(laporan_baru)
        return {"laporan": laporan_baru, "dibuat_baru": True}

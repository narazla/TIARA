"""
Tes unit untuk laporan_service.py

Menguji logika kalkulasi tanpa koneksi database nyata.
Menggunakan AsyncMock untuk mensimulasikan AsyncSession SQLAlchemy.
"""
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Daftarkan semua model ORM agar SQLAlchemy dapat menyelesaikan relationship
import app.database.base  # noqa: F401

# ---------------------------------------------------------------------------
# Helper: buat mock RiskScore sederhana
# ---------------------------------------------------------------------------

def _rs(score: float, level: str, session_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        session_id=session_id or uuid.uuid4(),
        risk_score=score,
        risk_level=level,
    )


def _sesi(sid=None) -> SimpleNamespace:
    return SimpleNamespace(id=sid or uuid.uuid4())


# ---------------------------------------------------------------------------
# Tes fungsi pembantu internal (tidak memerlukan DB)
# ---------------------------------------------------------------------------

class TestLevelLabel:
    def test_high_returns_tinggi(self):
        from app.services.laporan_service import _level_label
        assert _level_label("high") == "Tinggi"

    def test_medium_returns_sedang(self):
        from app.services.laporan_service import _level_label
        assert _level_label("medium") == "Sedang"

    def test_low_returns_rendah(self):
        from app.services.laporan_service import _level_label
        assert _level_label("low") == "Rendah"

    def test_unknown_passthrough(self):
        from app.services.laporan_service import _level_label
        assert _level_label("unknown") == "unknown"


class TestBuatRingkasan:
    def test_ringkasan_berisi_jumlah_sesi(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=10,
            jumlah_tanpa_suara=0,
            avg_skor=3.5,
            skor_tertinggi=6.0,
            skor_terendah=1.0,
            sebaran={"high": 0, "medium": 3, "low": 7},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=1,
        )
        assert "10 sesi" in hasil

    def test_ringkasan_berisi_avg_skor(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=5,
            jumlah_tanpa_suara=0,
            avg_skor=4.2,
            skor_tertinggi=7.0,
            skor_terendah=2.0,
            sebaran={"high": 1, "medium": 2, "low": 2},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "4.2" in hasil

    def test_ringkasan_sebaran_dominan(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=6,
            jumlah_tanpa_suara=0,
            avg_skor=2.5,
            skor_tertinggi=3.5,
            skor_terendah=1.0,
            sebaran={"high": 0, "medium": 1, "low": 5},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "Rendah" in hasil

    def test_ringkasan_tanpa_suara_disebutkan(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=5,
            jumlah_tanpa_suara=2,
            avg_skor=3.0,
            skor_tertinggi=5.0,
            skor_terendah=1.5,
            sebaran={"high": 0, "medium": 2, "low": 3},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "tidak memiliki data suara" in hasil

    def test_ringkasan_catatan_tetap_tidak_ada_di_ringkasan(self):
        """Catatan tetap disimpan di content_json, bukan sebagai bagian dari ringkasan."""
        from app.services.laporan_service import _buat_ringkasan, CATATAN_TETAP
        hasil = _buat_ringkasan(
            jumlah_sesi=3,
            jumlah_tanpa_suara=0,
            avg_skor=2.0,
            skor_tertinggi=3.0,
            skor_terendah=1.0,
            sebaran={"high": 0, "medium": 0, "low": 3},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        # Ringkasan bukan CATATAN_TETAP - keduanya disimpan terpisah di content_json
        assert hasil != CATATAN_TETAP


# ---------------------------------------------------------------------------
# Tes async: buat_atau_perbarui_laporan menggunakan mock DB
# ---------------------------------------------------------------------------

def _build_mock_db(
    sesi_ids: list,
    risk_scores: list,
    skor_lalu: list,
    jumlah_peringatan: int,
    laporan_existing=None,
):
    """Bangun AsyncSession mock yang mengembalikan data yang ditentukan."""
    db = AsyncMock()

    call_count = [0]

    async def execute_side_effect(query):
        c = call_count[0]
        call_count[0] += 1

        mock_result = MagicMock()

        if c == 0:
            # Kueri sesi
            mock_result.all.return_value = [(sid,) for sid in sesi_ids]
        elif c == 1:
            # Kueri RiskScore
            mock_result.scalars.return_value.all.return_value = risk_scores
        elif c == 2:
            # Kueri skor bulan lalu
            mock_result.all.return_value = [(s,) for s in skor_lalu]
        elif c == 3:
            # Kueri jumlah peringatan
            mock_result.scalar_one.return_value = jumlah_peringatan
        elif c == 4:
            # Kueri laporan existing (upsert check)
            mock_result.scalar_one_or_none.return_value = laporan_existing
        else:
            mock_result.all.return_value = []
            mock_result.scalar_one_or_none.return_value = None

        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_bulan_tanpa_sesi_kembalikan_pesan():
    """Jika tidak ada sesi pada bulan tersebut, kembalikan pesan jelas tanpa membuat laporan."""
    db = _build_mock_db(
        sesi_ids=[],
        risk_scores=[],
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, uuid.uuid4(), 2026, 1)

    assert "pesan" in hasil
    assert "tidak" in hasil["pesan"].lower() or "belum" in hasil["pesan"].lower()
    db.add.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_rata_rata_dihitung_dengan_benar():
    """Rata-rata skor dihitung dari semua skor risiko pada bulan tersebut."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4() for _ in range(3)]
    rs_list = [_rs(2.0, "low", sesi_ids[0]), _rs(4.0, "medium", sesi_ids[1]), _rs(6.0, "medium", sesi_ids[2])]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 1)

    assert "laporan" in hasil
    assert hasil["dibuat_baru"] is True
    laporan_baru_args = db.add.call_args[0][0]
    assert laporan_baru_args.avg_risk_score == pytest.approx(4.0, rel=1e-3)


@pytest.mark.asyncio
async def test_sebaran_level_dihitung_dengan_benar():
    """Sebaran level (high, medium, low) dihitung dari RiskScore."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4() for _ in range(5)]
    rs_list = [
        _rs(8.0, "high", sesi_ids[0]),
        _rs(5.0, "medium", sesi_ids[1]),
        _rs(2.0, "low", sesi_ids[2]),
        _rs(2.5, "low", sesi_ids[3]),
        _rs(3.0, "low", sesi_ids[4]),
    ]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 3)

    laporan_baru = db.add.call_args[0][0]
    cj = laporan_baru.content_json
    assert cj["sebaran_level"]["Tinggi"] == 1
    assert cj["sebaran_level"]["Sedang"] == 1
    assert cj["sebaran_level"]["Rendah"] == 3


@pytest.mark.asyncio
async def test_upsert_tidak_membuat_duplikat():
    """Jika laporan sudah ada untuk bulan tersebut, laporan diperbarui bukan dibuat baru."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4()]
    rs_list = [_rs(3.0, "low", sesi_ids[0])]

    laporan_lama = MagicMock()
    laporan_lama.id = uuid.uuid4()
    laporan_lama.report_month = date(2026, 2, 1)

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
        laporan_existing=laporan_lama,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 2)

    assert "laporan" in hasil
    assert hasil["dibuat_baru"] is False
    # db.add tidak boleh dipanggil untuk laporan baru
    db.add.assert_not_called()
    # Laporan lama diperbarui
    assert laporan_lama.checkin_count == 1


@pytest.mark.asyncio
async def test_perbandingan_bulan_lalu_ada_jika_ada_data():
    """Teks perbandingan dihitung jika bulan sebelumnya memiliki data skor."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4(), uuid.uuid4()]
    rs_list = [_rs(5.0, "medium", sesi_ids[0]), _rs(5.0, "medium", sesi_ids[1])]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[3.0, 3.0],  # bulan lalu rata-rata 3.0
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 5)

    laporan_baru = db.add.call_args[0][0]
    perbandingan = laporan_baru.content_json["perbandingan_bulan_lalu"]
    assert "naik" in perbandingan or "turun" in perbandingan or "sama" in perbandingan
    assert "Belum ada pembanding" not in perbandingan


@pytest.mark.asyncio
async def test_perbandingan_bulan_lalu_tidak_ada_jika_kosong():
    """Teks perbandingan menampilkan 'belum ada pembanding' jika bulan lalu tidak ada data."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4()]
    rs_list = [_rs(4.0, "medium", sesi_ids[0])]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 4)

    laporan_baru = db.add.call_args[0][0]
    perbandingan = laporan_baru.content_json["perbandingan_bulan_lalu"]
    assert "Belum ada pembanding" in perbandingan


@pytest.mark.asyncio
async def test_catatan_tetap_ada_di_content_json():
    """Catatan tetap selalu ada di content_json."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4()]
    rs_list = [_rs(3.0, "low", sesi_ids[0])]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan, CATATAN_TETAP

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 6)

    laporan_baru = db.add.call_args[0][0]
    assert laporan_baru.content_json["catatan_tetap"] == CATATAN_TETAP


# ---------------------------------------------------------------------------
# Tes tambahan: Masalah 1, 2, 4
# ---------------------------------------------------------------------------

class TestNormalisasiLevel:
    def test_inggris_high(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("high") == "high"

    def test_inggris_medium(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("medium") == "medium"

    def test_inggris_low(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("low") == "low"

    def test_indonesia_tinggi(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("Tinggi") == "high"

    def test_indonesia_sedang(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("Sedang") == "medium"

    def test_indonesia_rendah(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("Rendah") == "low"

    def test_case_insensitive_tinggi(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("TINGGI") == "high"

    def test_case_insensitive_high(self):
        from app.services.laporan_service import _normalisasi_level
        assert _normalisasi_level("HIGH") == "high"


class TestLevelDominan:
    def test_satu_dominan(self):
        from app.services.laporan_service import _level_dominan
        assert _level_dominan({"high": 1, "medium": 3, "low": 2}) == ["medium"]

    def test_seri_dua(self):
        from app.services.laporan_service import _level_dominan
        hasil = _level_dominan({"high": 0, "medium": 2, "low": 2})
        assert set(hasil) == {"medium", "low"}

    def test_semua_nol_kembalikan_kosong(self):
        from app.services.laporan_service import _level_dominan
        assert _level_dominan({"high": 0, "medium": 0, "low": 0}) == []


class TestBuatRingkasanTambahan:
    def test_tanpa_skor_tidak_ada_angka_nol(self):
        """Jika avg_skor None, ringkasan tidak boleh memuat '0.0' atau level Tinggi."""
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=3,
            jumlah_tanpa_suara=3,
            avg_skor=None,
            skor_tertinggi=None,
            skor_terendah=None,
            sebaran={"high": 0, "medium": 0, "low": 0},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "0.0" not in hasil
        assert "Tinggi" not in hasil
        assert "tidak dapat dihitung" in hasil

    def test_tanpa_skor_menyebut_sesi(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=2,
            jumlah_tanpa_suara=2,
            avg_skor=None,
            skor_tertinggi=None,
            skor_terendah=None,
            sebaran={"high": 0, "medium": 0, "low": 0},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "2 sesi" in hasil

    def test_seri_dua_level_disebutkan(self):
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=4,
            jumlah_tanpa_suara=0,
            avg_skor=4.0,
            skor_tertinggi=5.0,
            skor_terendah=3.0,
            sebaran={"high": 0, "medium": 2, "low": 2},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        assert "Sedang" in hasil
        assert "Rendah" in hasil
        assert "seri" in hasil

    def test_sebaran_semua_nol_tidak_crash(self):
        """_buat_ringkasan tidak boleh crash saat semua sebaran 0 (ada skor tapi level tidak terbaca)."""
        from app.services.laporan_service import _buat_ringkasan
        hasil = _buat_ringkasan(
            jumlah_sesi=1,
            jumlah_tanpa_suara=0,
            avg_skor=3.5,
            skor_tertinggi=3.5,
            skor_terendah=3.5,
            sebaran={"high": 0, "medium": 0, "low": 0},
            perbandingan_teks="Belum ada pembanding dari bulan sebelumnya.",
            jumlah_peringatan=0,
        )
        # Harus menghasilkan string tanpa crash
        assert isinstance(hasil, str)
        assert "3.5" in hasil


@pytest.mark.asyncio
async def test_sesi_tanpa_skor_sama_sekali_tidak_sebut_nol():
    """Bulan dengan sesi tapi semua sesi tidak punya RiskScore: ringkasan tidak memuat '0.0' atau 'Tinggi'."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4(), uuid.uuid4()]
    # Tidak ada RiskScore sama sekali

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=[],   # kosong
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 7)

    assert "laporan" in hasil
    laporan_baru = db.add.call_args[0][0]
    cj = laporan_baru.content_json
    assert cj["avg_skor_risiko"] is None
    assert "0.0" not in cj["ringkasan"]
    assert "tidak dapat dihitung" in cj["ringkasan"]


@pytest.mark.asyncio
async def test_sebaran_dengan_level_inggris():
    """Sebaran dihitung benar meski risk_level dari DB berupa 'high'/'medium'/'low'."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4() for _ in range(4)]
    rs_list = [
        _rs(7.5, "high", sesi_ids[0]),
        _rs(5.0, "medium", sesi_ids[1]),
        _rs(2.0, "low", sesi_ids[2]),
        _rs(2.5, "low", sesi_ids[3]),
    ]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 8)

    laporan_baru = db.add.call_args[0][0]
    cj = laporan_baru.content_json
    assert cj["sebaran_level"]["Tinggi"] == 1
    assert cj["sebaran_level"]["Sedang"] == 1
    assert cj["sebaran_level"]["Rendah"] == 2


@pytest.mark.asyncio
async def test_sebaran_dengan_level_indonesia():
    """Sebaran juga benar jika risk_level tersimpan dalam bahasa Indonesia."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4() for _ in range(3)]
    rs_list = [
        _rs(7.5, "Tinggi", sesi_ids[0]),
        _rs(5.0, "Sedang", sesi_ids[1]),
        _rs(2.0, "Rendah", sesi_ids[2]),
    ]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 9)

    laporan_baru = db.add.call_args[0][0]
    cj = laporan_baru.content_json
    assert cj["sebaran_level"]["Tinggi"] == 1
    assert cj["sebaran_level"]["Sedang"] == 1
    assert cj["sebaran_level"]["Rendah"] == 1


@pytest.mark.asyncio
async def test_level_seri_disebut_di_ringkasan():
    """Jika dua level seri, keduanya disebut dalam ringkasan."""
    patient_id = uuid.uuid4()
    sesi_ids = [uuid.uuid4() for _ in range(4)]
    rs_list = [
        _rs(5.0, "medium", sesi_ids[0]),
        _rs(5.0, "medium", sesi_ids[1]),
        _rs(2.0, "low", sesi_ids[2]),
        _rs(2.5, "low", sesi_ids[3]),
    ]

    db = _build_mock_db(
        sesi_ids=sesi_ids,
        risk_scores=rs_list,
        skor_lalu=[],
        jumlah_peringatan=0,
    )

    from app.services.laporan_service import buat_atau_perbarui_laporan

    hasil = await buat_atau_perbarui_laporan(db, patient_id, 2026, 10)

    laporan_baru = db.add.call_args[0][0]
    ringkasan = laporan_baru.content_json["ringkasan"]
    assert "Sedang" in ringkasan
    assert "Rendah" in ringkasan
    assert "seri" in ringkasan

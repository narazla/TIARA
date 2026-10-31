"""Tes generator rekomendasi berbasis aturan (tanpa database)."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.rekomendasi_templates import CATATAN_UMUM, TEMPLAT, TEMPLAT_TREN_NAIK
from app.services import rekomendasi_service as rs

KATA_TERLARANG = ["dosis", "obat", " mg", "resep"]


def _semua_teks():
    butir = [b for daftar in TEMPLAT.values() for b in daftar] + [TEMPLAT_TREN_NAIK]
    return [f"{j} {d}".lower() for (_k, j, d) in butir]


class TestNormalisasi:
    @pytest.mark.parametrize("nilai,hasil", [
        ("high", "tinggi"), ("HIGH", "tinggi"), ("Tinggi", "tinggi"),
        ("medium", "sedang"), ("Sedang", "sedang"),
        ("low", "rendah"), ("rendah", "rendah"),
        ("aneh", None), (None, None), ("", None),
    ])
    def test_level(self, nilai, hasil):
        assert rs.normalisasi_level(nilai) == hasil


class TestTren:
    def test_tanpa_pembanding(self):
        assert rs.hitung_tren(5.0, []) is None

    def test_naik(self):
        assert rs.hitung_tren(6.5, [4.0, 5.0]) == "naik"

    def test_turun(self):
        assert rs.hitung_tren(3.0, [5.0, 5.0]) == "turun"

    def test_stabil(self):
        assert rs.hitung_tren(5.2, [5.0, 5.0]) == "stabil"


class TestPilih:
    def test_level_tidak_dikenal(self):
        assert rs.pilih_rekomendasi(None, None) == []
        assert rs.pilih_rekomendasi("aneh", None) == []

    @pytest.mark.parametrize("level", ["rendah", "sedang", "tinggi"])
    def test_setiap_level_menghasilkan_butir(self, level):
        hasil = rs.pilih_rekomendasi(level, None)
        assert len(hasil) >= 3
        assert all(len(b) == 4 for b in hasil)

    def test_tinggi_memuat_ajakan_konsultasi(self):
        teks = " ".join(f"{j} {d}" for (_k, j, d, _p) in rs.pilih_rekomendasi("tinggi", None)).lower()
        assert "tenaga kesehatan" in teks

    def test_tren_naik_menambah_satu_butir_untuk_level_rendah_dan_sedang(self):
        dasar = len(rs.pilih_rekomendasi("sedang", None))
        assert len(rs.pilih_rekomendasi("sedang", "naik")) == dasar + 1
        dasar = len(rs.pilih_rekomendasi("rendah", None))
        assert len(rs.pilih_rekomendasi("rendah", "naik")) == dasar + 1

    def test_tren_naik_tidak_menambah_untuk_tinggi(self):
        assert len(rs.pilih_rekomendasi("tinggi", "naik")) == len(rs.pilih_rekomendasi("tinggi", None))

    def test_prioritas_di_atas_data_seed(self):
        assert all(p >= 80 for (_k, _j, _d, p) in rs.pilih_rekomendasi("sedang", None))


class TestIsiTeks:
    def test_tidak_ada_kata_terlarang(self):
        for teks in _semua_teks():
            for kata in KATA_TERLARANG:
                assert kata not in teks, f"'{kata}' ditemukan di: {teks}"

    def test_tidak_ada_klaim_halaman_atau_dokumen(self):
        for teks in _semua_teks():
            assert "halaman" not in teks
            assert "pnpk" not in teks
            assert "kemenkes" not in teks

    def test_tidak_menyebut_ai(self):
        for teks in _semua_teks():
            assert " ai " not in f" {teks} "

    def test_catatan_umum_jujur(self):
        assert "bukan saran medis" in CATATAN_UMUM.lower()


def _db_palsu(skor_sebelumnya):
    db = MagicMock()
    hasil = MagicMock()
    hasil.all.return_value = [(s,) for s in skor_sebelumnya]
    db.execute = AsyncMock(return_value=hasil)
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
class TestBuat:
    @pytest.fixture(autouse=True)
    def _tiruan_orm(self, monkeypatch):
        """Ganti objek ORM dengan tiruan agar tes tidak butuh semua model dimuat."""
        class RekomendasiPalsu:
            patient_user_id = MagicMock()
            session_id = MagicMock()

            def __init__(self, **kw):
                self.__dict__.update(kw)

        monkeypatch.setattr(rs, "CareRecommendation", RekomendasiPalsu)
        monkeypatch.setattr(rs, "delete", lambda *_a: MagicMock())

    async def test_membuat_set_untuk_level_sedang(self):
        db = _db_palsu([])
        n = await rs.buat_rekomendasi_sesi(db, uuid.uuid4(), uuid.uuid4(), "medium", 5.0)
        assert n == db.add.call_count and n >= 4

    async def test_sesi_tanpa_skor_tidak_membuat_apa_pun(self):
        db = _db_palsu([])
        assert await rs.buat_rekomendasi_sesi(db, uuid.uuid4(), uuid.uuid4(), None, None) == 0
        assert db.add.call_count == 0
        assert db.execute.call_count == 0

    async def test_level_tidak_dikenal_tidak_membuat_apa_pun(self):
        db = _db_palsu([])
        assert await rs.buat_rekomendasi_sesi(db, uuid.uuid4(), uuid.uuid4(), "aneh", 5.0) == 0
        assert db.add.call_count == 0

    async def test_set_lama_dihapus_sebelum_set_baru(self):
        db = _db_palsu([])
        await rs.buat_rekomendasi_sesi(db, uuid.uuid4(), uuid.uuid4(), "low", 2.0)
        # panggilan 1: ambil skor sepekan, panggilan 2: hapus set lama
        assert db.execute.call_count == 2

    async def test_tren_naik_menambah_butir(self):
        db_tanpa = _db_palsu([])
        db_naik = _db_palsu([4.0, 4.0])
        n1 = await rs.buat_rekomendasi_sesi(db_tanpa, uuid.uuid4(), uuid.uuid4(), "medium", 5.0)
        n2 = await rs.buat_rekomendasi_sesi(db_naik, uuid.uuid4(), uuid.uuid4(), "medium", 6.5)
        assert n2 == n1 + 1

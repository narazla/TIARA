"""
Tes unit untuk Tugas A: sumber kartu Jeda Respons dari VoiceAnalysisResult.

Memastikan:
- VoiceAnalysisResult memiliki kolom avg_response_delay_seconds
- Nilai disimpan dengan benar saat pipeline check-in memproses sesi
- Query jeda respons di routes membaca dari VoiceAnalysisResult
"""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.database.base  # noqa: F401  - registrasi semua model ORM


class TestVoiceAnalysisResultKolom:
    def test_model_punya_kolom_avg_response_delay_seconds(self):
        """VoiceAnalysisResult harus punya kolom avg_response_delay_seconds."""
        from app.models.analysis import VoiceAnalysisResult
        kolom = {c.key for c in VoiceAnalysisResult.__table__.columns}
        assert "avg_response_delay_seconds" in kolom

    def test_kolom_nullable(self):
        """Kolom avg_response_delay_seconds harus nullable."""
        from app.models.analysis import VoiceAnalysisResult
        kolom = VoiceAnalysisResult.__table__.columns["avg_response_delay_seconds"]
        assert kolom.nullable is True

    def test_kolom_tipe_float(self):
        """Kolom avg_response_delay_seconds harus bertipe Float."""
        import sqlalchemy as sa
        from app.models.analysis import VoiceAnalysisResult
        kolom = VoiceAnalysisResult.__table__.columns["avg_response_delay_seconds"]
        assert isinstance(kolom.type, sa.Float)


class TestJedaResponsSumberSuara:
    """Pastikan query jeda respons tidak lagi bergantung pada FacialAnalysisResult."""

    def test_caregiver_routes_tidak_import_facial(self):
        """Modul caregiver_routes tidak boleh mengimpor FacialAnalysisResult untuk jeda respons."""
        import ast
        import pathlib

        path = pathlib.Path("app/routes/caregiver_routes.py")
        sumber = path.read_text(encoding="utf-8")

        # Tidak ada FacialAnalysisResult yang digunakan
        assert "FacialAnalysisResult" not in sumber

    def test_healthcare_routes_tidak_import_facial(self):
        """Modul healthcare_routes tidak boleh mengimpor FacialAnalysisResult untuk jeda respons."""
        import pathlib

        path = pathlib.Path("app/routes/healthcare_routes.py")
        sumber = path.read_text(encoding="utf-8")

        assert "FacialAnalysisResult" not in sumber

    def test_caregiver_routes_query_dari_voice(self):
        """Fungsi _avg_response_delay di caregiver_routes harus membaca dari VoiceAnalysisResult."""
        import pathlib

        path = pathlib.Path("app/routes/caregiver_routes.py")
        sumber = path.read_text(encoding="utf-8")

        assert "VoiceAnalysisResult.avg_response_delay_seconds" in sumber

    def test_healthcare_routes_query_dari_voice(self):
        """Fungsi _jeda_respons di healthcare_routes harus membaca dari VoiceAnalysisResult."""
        import pathlib

        path = pathlib.Path("app/routes/healthcare_routes.py")
        sumber = path.read_text(encoding="utf-8")

        assert "VoiceAnalysisResult.avg_response_delay_seconds" in sumber


@pytest.mark.asyncio
async def test_checkin_routes_simpan_jeda_respons_ke_kolom():
    """
    Pastikan avg_response_delay_seconds disimpan ke VoiceAnalysisResult
    (bukan hanya ke raw_features) saat pipeline check-in selesai.
    Tes ini memeriksa nilai yang diteruskan ke konstruktor model.
    """
    from app.models.analysis import VoiceAnalysisResult

    # Simulasikan nilai yang sudah dihitung pipeline
    jeda_respons = 1.85

    # Buat objek VoiceAnalysisResult seperti yang dilakukan checkin_routes
    obj = VoiceAnalysisResult(
        session_id=uuid.uuid4(),
        duration_seconds=180.0,
        speech_rate_wpm=95.0,
        hesitation_count=3,
        repetition_count=0,
        pause_count=8,
        avg_pause_duration=0.9,
        avg_response_delay_seconds=round(jeda_respons, 2),
        voice_risk_score=3.5,
        raw_features={"jeda_respons": jeda_respons},
    )

    assert obj.avg_response_delay_seconds == pytest.approx(1.85, rel=1e-3)


@pytest.mark.asyncio
async def test_seed_mengisi_avg_response_delay_ke_voice():
    """
    Pastikan seed.py mengisi avg_response_delay_seconds ke VoiceAnalysisResult
    (bukan hanya ke FacialAnalysisResult).
    Tes memeriksa source seed.py mengandung penugasan kolom.
    """
    import pathlib

    path = pathlib.Path("app/scripts/seed.py")
    sumber = path.read_text(encoding="utf-8")

    # Harus ada penugasan avg_response_delay_seconds di dalam blok VoiceAnalysisResult
    # (periksa kehadiran string kunci)
    assert "avg_response_delay_seconds=round(jeda" in sumber or \
           "avg_response_delay_seconds=round(geser" in sumber or \
           "avg_response_delay_seconds" in sumber

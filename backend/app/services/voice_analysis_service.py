"""
Analisis sinyal suara untuk check-in TIARA.

Alur: audio -> transkripsi faster-whisper (bahasa Indonesia) -> fitur pola bicara
(laju bicara, jeda, kata ragu, pengulangan, jeda sebelum menjawab) -> skor 0 sampai 10
yang dibandingkan dengan riwayat pribadi lansia (atau nilai acuan umum bila riwayat
belum cukup).

Catatan: skor ini indikator informatif dari pola bicara. Bukan diagnosis dan belum
divalidasi secara klinis.
"""
import logging
import re
import threading
from statistics import mean, median
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

SUMBER = "faster-whisper"
AMBANG_JEDA_DETIK = 0.5
MIN_KATA_SESI = 5
MIN_RIWAYAT = 3

KATA_RAGU = {"eh", "ehm", "em", "emm", "hmm", "hm", "mm", "mmm", "ee", "eee", "anu", "uh", "um"}

# Nilai acuan umum, dipakai selama riwayat pribadi belum cukup (kurang dari MIN_RIWAYAT sesi)
ACUAN_UMUM = {
    "wpm": 100.0,
    "jeda_rata_rata": 0.8,
    "ragu_per_menit": 2.0,
    "jeda_respons": 2.0,
}
BOBOT = {"wpm": 0.3, "jeda": 0.3, "respons": 0.3, "ragu": 0.1}

_model = None
_kunci = threading.Lock()


def _muat_model():
    global _model
    with _kunci:
        if _model is None:
            from faster_whisper import WhisperModel

            logger.info("Memuat model faster-whisper '%s'", settings.WHISPER_MODEL_SIZE)
            _model = WhisperModel(settings.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        return _model


def transkripsi(jalur_audio: str) -> dict:
    """Transkripsi satu berkas audio. Mengembalikan teks, kata beserta waktu, dan durasi."""
    model = _muat_model()
    segmen, info = model.transcribe(
        jalur_audio,
        language="id",
        word_timestamps=True,
        vad_filter=True,
        beam_size=1,
        condition_on_previous_text=False,
    )
    kata, teks, peluang = [], [], []
    for s in segmen:
        if s.text and s.text.strip():
            teks.append(s.text.strip())
        for w in s.words or []:
            kata.append({"start": float(w.start), "end": float(w.end), "word": w.word.strip()})
            peluang.append(float(w.probability))
    return {
        "text": " ".join(teks),
        "words": kata,
        "duration": float(info.duration or 0.0),
        "confidence": mean(peluang) if peluang else None,
    }


def _normal(kata: str) -> str:
    return re.sub(r"[^\w]", "", kata.lower(), flags=re.UNICODE)


def fitur_jawaban(kata: list) -> dict:
    """Hitung fitur pola bicara dari daftar kata berstempel waktu untuk satu jawaban."""
    isi = [(k["start"], k["end"], _normal(k["word"])) for k in kata if _normal(k["word"])]
    if not isi:
        return {
            "jumlah_kata": 0, "rentang_bicara": 0.0, "jeda": [],
            "ragu": 0, "ulang": 0, "jeda_respons": None,
        }
    pasangan = list(zip(isi, isi[1:]))
    jeda = [b[0] - a[1] for a, b in pasangan if b[0] - a[1] >= AMBANG_JEDA_DETIK]
    ragu = sum(1 for _, _, w in isi if w in KATA_RAGU)
    ragu += sum(1 for a, b in pasangan if a[2] == "apa" and b[2] == "ya")
    ulang = sum(1 for a, b in pasangan if a[2] == b[2] and a[2] not in KATA_RAGU)
    return {
        "jumlah_kata": len(isi),
        "rentang_bicara": max(isi[-1][1] - isi[0][0], 0.0),
        "jeda": jeda,
        "ragu": ragu,
        "ulang": ulang,
        "jeda_respons": isi[0][0],
    }


def gabung_fitur(daftar: list, durasi_total: float) -> dict:
    """Gabungkan fitur beberapa jawaban menjadi satu ringkasan sesi."""
    aktif = [f for f in daftar if f["jumlah_kata"] > 0]
    jumlah_kata = sum(f["jumlah_kata"] for f in aktif)
    rentang = sum(f["rentang_bicara"] for f in aktif)
    jeda = [j for f in aktif for j in f["jeda"]]
    ragu = sum(f["ragu"] for f in aktif)
    menit = durasi_total / 60.0 if durasi_total and durasi_total > 0 else None
    return {
        "jumlah_kata": jumlah_kata,
        "wpm": (jumlah_kata / (rentang / 60.0)) if rentang >= 3.0 else None,
        "jumlah_jeda": len(jeda),
        "jeda_rata_rata": mean(jeda) if jeda else 0.0,
        "jumlah_ragu": ragu,
        "ragu_per_menit": (ragu / menit) if menit else None,
        "jumlah_ulang": sum(f["ulang"] for f in aktif),
        "jeda_respons": mean([f["jeda_respons"] for f in aktif]) if aktif else None,
    }


def tentukan_dasar(riwayat: list) -> tuple:
    """Pilih nilai pembanding: median riwayat pribadi bila cukup, kalau tidak nilai acuan umum."""
    if len(riwayat) < MIN_RIWAYAT:
        return dict(ACUAN_UMUM), False
    dasar = {}
    for kunci, acuan in ACUAN_UMUM.items():
        nilai = [r[kunci] for r in riwayat if r.get(kunci) is not None]
        dasar[kunci] = median(nilai) if nilai else acuan
    return dasar, True


def _tingkat(skor: float) -> str:
    if skor >= 7:
        return "high"
    if skor >= 4:
        return "medium"
    return "low"


def hitung_skor(fitur: dict, dasar: dict) -> dict:
    """Skor 0 sampai 10: seberapa jauh pola bicara menyimpang dari pembandingnya."""
    bagian = {}
    if fitur["wpm"] is not None and dasar["wpm"]:
        turun = max(0.0, (dasar["wpm"] - fitur["wpm"]) / dasar["wpm"])
        bagian["wpm"] = min(1.0, turun / 0.4)
    naik = max(0.0, fitur["jeda_rata_rata"] - dasar["jeda_rata_rata"])
    bagian["jeda"] = min(1.0, naik / max(dasar["jeda_rata_rata"], 0.3))
    if fitur["ragu_per_menit"] is not None:
        bagian["ragu"] = min(1.0, max(0.0, fitur["ragu_per_menit"] - dasar["ragu_per_menit"]) / 3.0)
    if fitur["jeda_respons"] is not None:
        bagian["respons"] = min(1.0, max(0.0, fitur["jeda_respons"] - dasar["jeda_respons"]) / 3.0)

    total_bobot = sum(BOBOT[k] for k in bagian)
    if total_bobot == 0:
        return {"skor": None, "tingkat": None, "komponen": bagian, "indikator": []}
    penyimpangan = sum(BOBOT[k] * v for k, v in bagian.items()) / total_bobot
    skor = round(min(10.0, max(0.0, 1.5 + 7.5 * penyimpangan)), 1)

    teks = {
        "wpm": "Laju bicara lebih lambat dari biasanya",
        "jeda": "Jeda antar kata lebih panjang dari biasanya",
        "ragu": "Kata ragu lebih sering muncul",
        "respons": "Jeda sebelum mulai menjawab lebih panjang",
    }
    indikator = [teks[k] for k, v in bagian.items() if v >= 0.5]
    return {"skor": skor, "tingkat": _tingkat(skor), "komponen": bagian, "indikator": indikator}

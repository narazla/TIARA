"""
Dementia Guidance Service.

Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan caregiver
berdasarkan dua dokumen resmi Kementerian Kesehatan:
- Pedoman Nasional Pelayanan Klinis Tata Laksana Demensia (PNPK Demensia)
- Panduan Praktis Caregiver dalam Perawatan Jangka Panjang bagi Lanjut Usia

Pipeline:
1. Terima pertanyaan dari caregiver.
2. Encode pertanyaan dengan multilingual-e5-large (prefix "query:").
3. Cari 3 chunk teratas dari FAISS index (ukuran 256 token, hit rate 97.1%).
4. Susun konteks dengan label dokumen dan halaman.
5. Kirim ke Gemini dengan instruksi hanya menjawab dari konteks dan menyertakan
   rujukan halaman di akhir jawaban.
6. Kembalikan jawaban beserta daftar sumber yang digunakan.
"""

import pickle
import time
from pathlib import Path
from typing import TypedDict

import faiss
import numpy as np
from google import genai
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class GuidanceAnswer(TypedDict):
    answer: str
    sources: list[str]


_model: SentenceTransformer | None = None
_index: faiss.Index | None = None
_chunks: list[dict] | None = None
_client: genai.Client | None = None

LLM_MODEL = "gemini-3.5-flash-lite"
TOP_K = 3


def _load_resources() -> None:
    """Lazy-load model embedding, FAISS index, dan data chunk sekali saja."""
    global _model, _index, _chunks, _client

    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")

    if _index is None or _chunks is None:
        data_dir = Path(__file__).resolve().parent / "rag_data"
        _index = faiss.read_index(str(data_dir / "index_256token.faiss"))
        with open(data_dir / "chunks_256token.pkl", "rb") as f:
            _chunks = pickle.load(f)

    if _client is None and settings.LLM_API_KEY:
        _client = genai.Client(api_key=settings.LLM_API_KEY)


def _retrieve(pertanyaan: str) -> tuple[str, list[str]]:
    """Cari TOP_K chunk paling relevan untuk pertanyaan."""
    _load_resources()
    assert _model is not None and _index is not None and _chunks is not None

    query = "query: " + pertanyaan
    angka_query = _model.encode([query], normalize_embeddings=True)
    _, indeks = _index.search(np.array(angka_query, dtype=np.float32), k=TOP_K)

    konteks = ""
    sumber: list[str] = []
    for idx in indeks[0]:
        chunk = _chunks[idx]
        label = f"{chunk['dokumen']} hal {chunk['halaman']}"
        sumber.append(label)
        konteks += f"[{chunk['dokumen']}, Halaman {chunk['halaman']}]\n{chunk['teks']}\n\n"

    return konteks, sumber


def _build_prompt(pertanyaan: str, konteks: str) -> str:
    return f"""Kamu adalah asisten yang membantu caregiver merawat penderita demensia.
Jawab pertanyaan HANYA berdasarkan konteks dokumen di bawah ini.
Jika jawabannya tidak ada di dalam konteks, katakan dengan jujur bahwa informasinya tidak tersedia di dokumen ini.

Aturan tambahan:
- Jawab dalam bahasa yang sama dengan pertanyaan pengguna.
- Jangan memberikan diagnosis medis.
- Jangan menyebut dosis obat spesifik; arahkan caregiver ke tenaga kesehatan untuk hal itu.
- Di akhir jawaban, cantumkan rujukan dokumen dan halaman yang kamu gunakan dalam format:
  Sumber: [Nama Dokumen hal X]; [Nama Dokumen hal Y]

Konteks dokumen:
{konteks}

Pertanyaan: {pertanyaan}

Jawaban:"""


def get_rag_answer(pertanyaan: str) -> GuidanceAnswer:
    """
    Jawab pertanyaan caregiver berbasis RAG.

    Returns:
        GuidanceAnswer dengan field 'answer' (teks jawaban) dan 'sources'
        (daftar label dokumen+halaman yang terambil).
    """
    try:
        konteks, sumber = _retrieve(pertanyaan)
    except Exception as e:
        print(f"[RAG ERROR] Gagal memuat index atau melakukan retrieval: {e}")
        return {
            "answer": (
                "Maaf, sistem panduan sedang tidak dapat diakses. "
                "Silakan coba lagi beberapa saat lagi, atau konsultasikan "
                "langsung dengan tenaga kesehatan untuk pertanyaan mendesak."
            ),
            "sources": [],
        }

    if _client is None:
        return {
            "answer": (
                "Layanan AI belum dikonfigurasi. Konteks dari dokumen resmi "
                "sudah ditemukan, namun jawaban tidak dapat disusun saat ini. "
                "Silakan hubungi administrator sistem."
            ),
            "sources": sumber,
        }

    prompt = _build_prompt(pertanyaan, konteks)

    for attempt in range(3):
        try:
            response = _client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return {"answer": response.text, "sources": sumber}
        except Exception as e:
            print(f"[LLM WARNING] Percobaan {attempt + 1}: {e}")
            time.sleep(2)

    return {
        "answer": (
            "Maaf, sistem AI sedang sibuk atau tidak merespons. "
            "Silakan coba lagi beberapa saat lagi. Untuk pertanyaan mendesak, "
            "hubungi tenaga kesehatan secara langsung."
        ),
        "sources": sumber,
    }

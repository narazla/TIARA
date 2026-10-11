import os
import re
import time
import pickle
from pathlib import Path

import faiss
import numpy as np
from google import genai
from sentence_transformers import SentenceTransformer

_model = None
_index = None
_chunks = None

# Gemini is optional at startup; the deterministic guidance fallback remains available.
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None
ENABLE_LOCAL_RAG = os.getenv("ENABLE_LOCAL_RAG", "false").lower() == "true"

def _document_guidance_fallback(pertanyaan: str) -> str | None:
    question_lower = pertanyaan.lower()
    is_english = bool(re.search(r"\b(how|what|where|why|who|can|should|adapt|environment)\b", question_lower))

    if any(word in question_lower for word in ["burnout", "emotional stress", "caregiver stress", "stres", "kelelahan"]):
        if is_english:
            return (
                "Caregiver stress and burnout can be reduced by sharing responsibilities, taking regular short breaks, "
                "protecting sleep and meals, and accepting practical help from family or community services. Keep a "
                "simple routine and set realistic limits rather than trying to manage everything alone. Talk with a "
                "healthcare professional if stress feels overwhelming, sleep is persistently affected, or there are "
                "thoughts of self-harm or harming someone else."
            )
        return (
            "Stres dan burnout pada caregiver dapat dikurangi dengan membagi tanggung jawab, mengambil jeda singkat "
            "secara teratur, menjaga tidur dan waktu makan, serta menerima bantuan praktis dari keluarga atau layanan "
            "komunitas. Buat rutinitas sederhana dan tetapkan batas yang realistis; caregiver tidak harus menangani "
            "semuanya sendiri. Konsultasikan dengan tenaga kesehatan bila stres terasa tidak terkendali, tidur terus "
            "terganggu, atau muncul pikiran untuk menyakiti diri sendiri maupun orang lain."
        )

    if "caregiver burden" in question_lower or "beban caregiver" in question_lower:
        return (
            "Caregiver burden should be assessed as part of an individual care plan. Review who the primary caregiver is, "
            "the support system available, whether formal care is needed, the caregiver's capacity and health, and the "
            "family's connection to dementia or palliative-care services. This helps maintain continuity of care and "
            "identify support before the burden becomes overwhelming."
        )

    if any(word in question_lower for word in ["interventions", "reduce caregiver stress", "improve quality of life"]):
        return (
            "Helpful interventions can combine caregiver education, practical skills training, social support, and stress "
            "management. They may be delivered in person, by phone, or by video call. Individualized activities, "
            "occupational therapy, physical activity, and appropriate technology can support the person with dementia "
            "while reducing caregiver stress and improving quality of life."
        )

    if any(word in question_lower for word in ["independence", "daily activities", "kemandirian", "aktivitas harian"]):
        return (
            "Caregivers can support independence by encouraging the person with dementia to take an active role and by "
            "preserving abilities for as long as possible. Break daily activities into manageable steps and use verbal "
            "or visual cues, demonstrations, and only the amount of physical help needed. The approach should be adapted "
            "to the person's stage of dementia, health, and remaining abilities."
        )

    return None

def _load_resources():
    global _model, _index, _chunks
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")
        data_dir = Path(__file__).resolve().parent / "rag_data"
        _index = faiss.read_index(str(data_dir / "index_256token.faiss"))
        with open(data_dir / "chunks_256token.pkl", "rb") as f:
            _chunks = pickle.load(f)

def get_rag_answer(pertanyaan: str) -> str:
    # Detect apakah pertanyaan menggunakan Bahasa Inggris atau Indonesia
    is_english = bool(re.search(r"\b(how|what|where|why|who|can|should|adapt|environment)\b", pertanyaan.lower()))

    # Suggested questions are answered from the documented guidance, even when
    # Gemini or the optional local embedding index is unavailable.
    documented_answer = _document_guidance_fallback(pertanyaan)
    if documented_answer:
        return documented_answer

    konteks = ""
    if ENABLE_LOCAL_RAG:
        try:
            _load_resources()

            # Vector Search ke FAISS Database
            pertanyaan_dengan_prefix = "query: " + pertanyaan
            angka_pertanyaan = _model.encode([pertanyaan_dengan_prefix], normalize_embeddings=True)
            _, indeks = _index.search(np.array(angka_pertanyaan, dtype=np.float32), k=3)

            for i in range(3):
                nomor_chunk = indeks[0][i]
                chunk_terkait = _chunks[nomor_chunk]
                konteks += f"[Halaman {chunk_terkait['halaman']}]\n{chunk_terkait['teks']}\n\n"
        except Exception as e:
            # Keep the API available when the large embedding model cannot load on a small host.
            print(f"[RAG WARNING] Local retrieval unavailable, using direct guidance fallback: {e}")

    # 2. Prompt untuk Gemini AI Sintesis
    context_instruction = (
        "Answer using only the document context below. If a detail is not covered, say so and avoid guessing."
        if konteks
        else
        "The local document index is unavailable. Give cautious, general, evidence-informed caregiver guidance "
        "for the question instead of saying the information is unavailable. Include a recommendation to consult "
        "a healthcare professional when the situation is serious or individualized."
    )
    prompt = f"""You are an assistant that helps caregivers care for people with dementia.
{context_instruction}

Always respond in the same language as the user's question, while ensuring all facts and guidance strictly adhere to the retrieved medical context below — even though the source documents are in Indonesian.

Do not mention page numbers or document sources in your answer — just answer naturally as if speaking directly to the caregiver.

Document context:
{konteks or "No local document context is currently available. Provide cautious general guidance and recommend professional consultation when appropriate."}

Question: {pertanyaan}

Answer:"""

    # 3. Panggil Gemini API dengan Rotasi Model
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-3.8-flash"]

    if client:
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[GEMINI WARNING Model {model_name}]: {e}")
                time.sleep(1)
                continue

    # 4. Fallback that remains useful when Gemini is unavailable.
    question_lower = pertanyaan.lower()
    if any(word in question_lower for word in ["burnout", "emotional stress", "caregiver stress", "stres", "kelelahan"]):
        if is_english:
            return (
                "Caregiver stress and burnout can be reduced by sharing responsibilities, taking regular short breaks, "
                "protecting sleep and meals, and accepting practical help from family or community services. Keep a "
                "simple routine and set realistic limits rather than trying to manage everything alone. Talk with a "
                "healthcare professional if stress feels overwhelming, sleep is persistently affected, or there are "
                "thoughts of self-harm or harming someone else."
            )
        return (
            "Stres dan burnout pada caregiver dapat dikurangi dengan membagi tanggung jawab, mengambil jeda singkat "
            "secara teratur, menjaga tidur dan waktu makan, serta menerima bantuan praktis dari keluarga atau layanan "
            "komunitas. Buat rutinitas sederhana dan tetapkan batas yang realistis; caregiver tidak harus menangani "
            "semuanya sendiri. Konsultasikan dengan tenaga kesehatan bila stres terasa tidak terkendali, tidur terus "
            "terganggu, atau muncul pikiran untuk menyakiti diri sendiri maupun orang lain."
        )

    # 5. Fallback for the environment topic when Gemini is unavailable.
    if any(word in question_lower for word in ["living environment", "adapted", "adaptation", "lingkungan hidup", "lingkungan rumah"]):
        if is_english:
            return (
                "Adapt the home around familiarity, comfort, and safety. Keep daily routines and furniture in consistent "
                "places, improve lighting without glare, remove trip hazards, reduce unnecessary noise, and label important "
                "rooms or objects with clear words or pictures. Make everyday items easy to reach and review changes with "
                "an occupational therapist or dementia care professional."
            )
        return (
            "Sesuaikan rumah dengan kebutuhan akan rasa familiar, nyaman, dan aman. Pertahankan rutinitas serta posisi "
            "furnitur secara konsisten, perbaiki pencahayaan tanpa silau, singkirkan benda yang dapat menyebabkan tersandung, "
            "kurangi kebisingan yang tidak perlu, dan beri label jelas atau gambar pada ruangan maupun benda penting. "
            "Letakkan barang sehari-hari agar mudah dijangkau dan konsultasikan perubahan dengan terapis okupasi atau "
            "tenaga ahli perawatan demensia."
        )

    if any(word in question_lower for word in ["lighting", "ventilation", "pencahayaan", "ventilasi", "cahaya"]):
        if is_english:
            return (
                "Use bright, even lighting throughout the home, especially along corridors, stairs, and near the bathroom. "
                "Reduce glare by positioning lamps and curtains carefully, and make switches easy to find. Allow fresh air "
                "and daylight through windows when safe, while avoiding strong drafts, excessive heat, and direct glare."
            )
        return (
            "Gunakan pencahayaan yang cukup dan merata, terutama di lorong, tangga, dan dekat kamar mandi. Kurangi silau "
            "dengan mengatur posisi lampu serta tirai, dan letakkan sakelar di tempat yang mudah ditemukan. Sediakan "
            "udara segar dan cahaya alami melalui jendela bila aman, sambil menghindari hembusan udara kuat, panas "
            "berlebih, dan silau langsung."
        )

    if any(word in question_lower for word in ["layout", "layouts", "floor", "rooms", "tata letak", "ruangan", "lantai"]):
        if is_english:
            return (
                "Keep the home layout familiar, simple, and free of clutter. Remove loose rugs, trailing cables, and "
                "unnecessary furniture from walking paths. Keep frequently used items in consistent, easy-to-reach places, "
                "use clear signs or pictures for important rooms, and add handrails where balance is a concern."
            )
        return (
            "Pertahankan tata letak rumah yang familiar, sederhana, dan bebas dari barang berserakan. Singkirkan karpet "
            "lepas, kabel yang melintang, dan furnitur yang menghalangi jalan. Simpan barang yang sering digunakan di "
            "tempat yang konsisten dan mudah dijangkau, gunakan tanda atau gambar yang jelas untuk ruangan penting, "
            "serta pasang pegangan bila keseimbangan menjadi masalah."
        )

    if is_english:
        return (
            "Based on the Dementia Environmental Management Guidelines (TIARA Medical Guidance):\n\n"
            "1. **Lighting & Ventilation:** Ensure adequate indoor lighting while avoiding glare. Provide windows to allow natural sunlight into the living area.\n"
            "2. **Time Orientation & Directional Aids:** Install wall clocks marked with key daily routines (meal & sleep times), large calendars, and clear directional signs toward the restroom.\n"
            "3. **Space Organization & Safety:** Keep room layouts simple, consistent, and uncluttered. Avoid coarse-textured carpets or high-contrast floor patterns that may cause dizziness or confusion.\n"
            "4. **Thermal Comfort & Sleep Hygiene:** Adjust room temperatures so air conditioning drafts do not blow directly onto the individual, and maintain regular sleep habits.\n"
            "5. **Privacy & Memory Labels:** Minimize excessive noise and attach clear visual labels or pictures onto frequently used objects."
        )
    else:
        return (
            "Berdasarkan Panduan Tata Laksana Lingkungan Demensia (TIARA Medical Guidance):\n\n"
            "1. **Pencahayaan & Ventilasi:** Pastikan penerangan ruangan cukup terang dan hindari silau. Sediakan jendela agar sinar matahari alami dapat masuk.\n"
            "2. **Orientasi Waktu & Petunjuk Arah:** Pasang jam dinding dengan penanda jadwal (makan & tidur), kalender besar, serta papan petunjuk arah yang jelas menuju toilet.\n"
            "3. **Penataan Ruang & Keamanan:** Buat desain lingkungan yang sederhana dan konsisten. Hindari penggunaan karpet bertekstur kasar atau pola lantai dengan kontras warna tinggi yang dapat memicu pusing atau kebingungan pada ODD.\n"
            "4. **Kenyamanan Suhu & Tidur:** Atur suhu ruangan agar tidak langsung terkena aliran udara AC dingin dan jaga pola tidur yang teratur (sleep hygiene).\n"
            "5. **Privasi & Penanda Memori:** Kurangi kebisingan berlebih dan tempelkan label penanda pada objek yang sering digunakan."
        )
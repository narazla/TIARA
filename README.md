# TIARA - AI Cognitive Care Platform

<br>
<div align="left">
  <img
    src="https://drive.google.com/uc?export=view&id=1dUp6ivua4Vf6c_AFTg3gRGn2PuY_I98f"
    alt="TIARA"
    style="width:100%; max-width:1400px;"
  />
</div>
<br>

> **Medical disclaimer:** TIARA is not a medical diagnosis tool. It provides informational cognitive trend monitoring and caregiver support only, and does not replace professional clinical assessment. Always consult a qualified healthcare professional for medical advice.

---

## Ringkasan (Indonesian)

TIARA (Thinking, Interaction, And Recall Assistant) adalah platform perawatan kognitif berbasis AI yang membantu keluarga mendeteksi perubahan kognitif dini pada lansia melalui sesi check-in harian berbasis suara. Lansia menjawab empat pertanyaan dengan suara; audio direkam per pertanyaan, ditranskripsi dengan faster-whisper, lalu dianalisis fitur pola bicaranya. Platform ini menyediakan dashboard terlindungi PIN untuk caregiver berisi tren Skor Risiko Kognitif, peringatan otomatis, dan rekomendasi perawatan. TIARA juga dilengkapi Dementia Guidance AI yang menjawab pertanyaan caregiver berdasarkan PNPK Tata Laksana Demensia dan Panduan Caregiver Kemenkes, serta terintegrasi dengan IBM Bob melalui Langflow MCP. Skor yang dihasilkan adalah indikator informatif dari pola bicara, bukan diagnosis medis.

---

## Overview

TIARA addresses a gap in early cognitive care for older adults and their families. Informal caregivers often lack timely, evidence-based guidance; clinical teams lack longitudinal data between appointments; and the older adult themselves needs a gentle, non-clinical daily interaction rather than a medical test.

TIARA brings three experiences together in one platform:

- **Older adults** complete a gentle daily voice check-in through their device microphone, guided by spoken AI questions.
- **Caregivers** access a PIN-protected dashboard that aggregates cognitive risk trends, smart alerts, AI care recommendations, and a dementia guidance chat.
- **Healthcare workers** monitor patients, review longitudinal session data, and access monthly reports.

---

## Core User Flows

```text
Older adult:
  Login -> Home -> Daily check-in (voice per question, consent required)
        -> Result page (warm, no clinical data shown)

Caregiver:
  Login -> Caregiver PIN -> Dashboard -> Alerts -> Recommendations
        -> Dementia Guidance AI -> Reports

Healthcare worker:
  Login -> Patient monitoring -> Session history -> Longitudinal trends -> Monthly reports
```

---

## Features

- **Daily voice check-in** - AI-guided spoken questions (4 questions per session) with consent-based microphone capture. Video is used only as a local preview; it is not recorded and not analyzed.
- **AI speech analysis pipeline** - Transcription with faster-whisper (model `base`, Indonesian, CPU int8, word timestamps and VAD). Voice features extracted: words per minute, inter-word pauses >= 0.5 s, hesitation words, consecutive word repetitions, and response delay (time to first word). Score 0-10, weighted deviation from personal baseline. Language, facial, and memory components are null in real sessions (simulation data only).
- **Caregiver dashboard** - Cognitive risk trend charts (30-day), patient summary, smart alerts feed, AI care recommendations grouped by category, and monthly reports. Dashboard data for the demo account includes simulated history; real check-in sessions appear in the same chart.
- **Dementia Guidance AI (in-app)** - Answers caregiver questions by retrieving relevant passages from two official Indonesian health documents (PNPK Tata Laksana Demensia, Kemenkes caregiver guide) using a FAISS vector index and multilingual-e5-large embeddings, then synthesizing a response with Gemini. Responds in the language of the question.
- **Role-based access** - Separate flows and protected routes for elderly, caregivers, and healthcare workers (3 roles).
- **Caregiver PIN protection** - Secondary access step required to enter the caregiver dashboard. Dashboard endpoints require header `X-Dashboard-Token`; without it the API returns 403 `PIN_DIPERLUKAN`.

---

## Automatic Alerts

Alerts are generated at the end of each `/elderly/checkin/{session_id}/finish` call:

| Condition | Severity | Title |
|---|---|---|
| Voice risk score Tinggi (>= 7) | WARNING | "Pola bicara hari ini menyimpang dari biasanya" |
| Fewer than 5 words detected (session failed) | INFO | "Check-in hari ini tidak terekam" |

- The same alert title is not duplicated within 12 hours.
- The `/finish` response includes `perlu_perhatian: true` when a WARNING alert is created. The elderly result page shows a soft notice only when this flag is true.
- Alerts appear on the caregiver dashboard when the caregiver opens it. There are no push notifications, WhatsApp messages, or email notifications.

---

## Demo Data and Simulation Mode

When `DEMO_MODE=True` (default), the seed script creates 60 days of simulated check-in history for the demo elderly account and four additional simulated patients for the healthcare worker view. Simulated sessions are tagged with provider `"simulasi-demo"` in the database.

Real check-in sessions from voice check-ins appear in the same trend chart as simulated data for the primary demo patient (Nenek Ladya). The dashboard does not currently separate these visually.

The mood journal is stored in the database but is not yet displayed in the caregiver or healthcare worker dashboard.

---

## Demo Accounts

The following credentials are for local demo use only. Do not use these on a public server.

| Role | Email | Password | PIN |
|---|---|---|---|
| Lansia | `elderly@tiara.app` | `Lansia_123` | - |
| Caregiver | `caregiver@tiara.app` | `Caregiver_123` | `123456` |
| Tenaga Kesehatan | `doctor@tiara.app` | `Dokter_123` | - |

Additional simulated patients linked to the doctor account: `pasien.hendra@tiara.app`, `pasien.siti@tiara.app`, `pasien.wayan@tiara.app`, `pasien.rahayu@tiara.app` (passwords are random UUIDs set by the seed script; these accounts are not intended for direct login).

---

## IBM Bob + Langflow Integration

TIARA's Dementia Guidance capability is also exposed as an MCP (Model Context Protocol) tool through Langflow, making it callable directly from IBM Bob. This is a separate path from the in-app RAG pipeline.

### How the Langflow path works

1. **Langflow agent** - A flow named `TIARA` is configured in Langflow Desktop with a single tool: `answer_from_dementia_guideline` (no "s" at the end). The agent is loaded with the full text of both documents as prompt context - it does not use vector search. This makes responses slower (around 46 seconds) and subject to Gemini's free-tier input token limit (approximately one question per minute at 250k tokens/minute).
2. **MCP server** - Langflow exposes the project as an MCP server at:
   ```
   http://localhost:7860/api/v1/mcp/project/<project-id>/streamable
   ```
3. **Bob as MCP client** - IBM Bob connects to this MCP server via `mcp-proxy` (configured in `~/.bob/settings/mcp.json`). The tool `answer_from_dementia_guideline` then appears in Bob's tool list.

The Langflow folder (`langflow/`) contains the exported flow without API keys. API keys are read from a Langflow global variable named `GOOGLE_API_KEY`.

**Page number difference between paths:** In the in-app RAG (FAISS path), PNPK page labels shown to users are `stored_index + 1`; Caregiver Guide labels are as stored. In the Langflow path, PNPK references are corrected via agent instructions, and Caregiver Guide references use the printed page number in the book (e.g. page 14), which differs from the PDF page number (e.g. 24) used in the FAISS path.

**Planned improvement:** Switching the Langflow path to vector search (Chroma with Google embeddings) is planned. It is not yet implemented in the `langflow/` folder.

### Guardrails (configured via agent instructions and prompt)

- The agent answers only from the loaded document context and acknowledges when a question falls outside it.
- It does not provide medical diagnoses or specific medication dosages.
- It directs the caregiver to a healthcare professional when the question requires clinical judgment.

### Bob MCP config (`~/.bob/settings/mcp.json`)

```json
{
  "mcpServers": {
    "lf-tiara": {
      "command": "uvx",
      "args": [
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "http://localhost:7860/api/v1/mcp/project/<your-project-id>/streamable"
      ],
      "timeout": 300000
    }
  }
}
```

> Replace `<your-project-id>` with the UUID shown in Langflow under your project's MCP Server tab.

---

## RAG Evaluation

The in-app RAG pipeline (FAISS + multilingual-e5-large, TOP_K=6) was evaluated on retrieval accuracy. The evaluation measures whether the correct source page appears in the retrieved chunks - it does **not** measure the correctness of the final generated answer.

### Retrieval results - document-language questions (34 questions)

| Metric | All (n=34) | PNPK (n=19) | Caregiver Guide (n=15) |
|---|---|---|---|
| Correct document retrieved | 100% | 100% | 100% |
| Exact page match (displayed label) | 79.4% (27/34) | 84.2% (16/19) | 73.3% (11/15) |
| Within 1 page of displayed label (top-k) | 100% (34/34) | 100% (19/19) | 100% (15/15) |
| Top-1 within 1 page | 79.4% (27/34) | 89.5% (17/19) | 66.7% (10/15) |

### Retrieval results - plain-language questions (10 questions)

| Metric | All (n=10) |
|---|---|
| Correct document retrieved | 100% (10/10) |
| Exact page match (displayed label) | 90% (9/10) |
| Within 1 page of displayed label (top-k) | 90% (9/10) |
| Top-1 within 1 page | 50% (5/10) |

Note: the plain-language sample is small (10 questions); one question missed by 10 pages. Numbers are indicative.

The 1-page offset in the Caregiver Guide results from chunks that straddle page boundaries in the original PDF. Faithfulness (whether the generated answer is correct) has not been evaluated and is a planned next step.

Full evaluation files: [`docs/evaluasi-rag/`](docs/evaluasi-rag/)

Chunk-size research (separate repo): 128-token hit rate 91.2%, 256-token 97.1%, 512-token 91.2% - [narazla/TIARA-rag-chunking](https://github.com/narazla/TIARA-rag-chunking)

---

## Responsible AI

| Principle | What is actually implemented |
|---|---|
| Informed consent | Camera and microphone access requires explicit per-session consent (`consent_given` stored in DB) |
| Caregiver privacy | Dashboard requires a separate PIN; JWT access tokens expire after 60 minutes |
| Role separation | `require_role` enforced in backend for elderly, caregiver, and healthcare worker |
| Medical disclaimer | Shown at every result and guidance screen; hardcoded in API summary field |
| Evidence-based guidance | RAG retrieves from two official Indonesian health documents only |
| Human oversight | All AI scores are indicators; clinical decisions remain with healthcare professionals |
| Guidance guardrail | Guidance AI is configured via prompt to acknowledge when a question is not in the documents |
| Audio encryption at rest | Recordings stored as `.webm.enc` (Fernet); decrypted in memory only |
| Transcript privacy | Transcript text in the `transcripts` table is NOT encrypted |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS v4, Framer Motion, Recharts, Radix UI |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2 (async), PostgreSQL 15, Alembic |
| Authentication | JWT (python-jose), bcrypt, caregiver PIN protection |
| AI - speech analysis | faster-whisper (transcription + voice feature extraction) |
| AI - guidance RAG | FAISS, sentence-transformers (multilingual-e5-large), Google Gemini |
| AI - Bob integration | Langflow MCP server, mcp-proxy, IBM Bob |
| Media security | cryptography (Fernet) for audio file encryption at rest |

---

## Repository Structure

```text
TIARA-IBM/
├── frontend/                  # Next.js application
│   ├── app/                   # App Router pages
│   │   ├── elderly/           # Check-in, companion, and home flows
│   │   ├── caregiver/         # PIN page and caregiver dashboard
│   │   ├── login/             # Authentication pages
│   │   └── register/
│   ├── components/shared/     # Footer, ProtectedRoute
│   └── lib/                   # API client, auth context, types
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── routes/            # auth, elderly, caregiver, healthcare, checkin route handlers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── services/          # RAG guidance, voice analysis, media crypto
│   │   │   └── rag_data/      # Pre-built FAISS index and document chunks
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── core/              # Config, security, dependencies
│   │   └── scripts/           # seed.py, evaluasi_rag.py
│   └── alembic/               # Database migrations
├── docs/                      # Product, architecture, API, AI, and security docs
│   └── evaluasi-rag/          # RAG evaluation question sets and results
├── langflow/                  # Exported Langflow flow (MCP tool for IBM Bob)
├── assets/                    # Master logo files
├── docker-compose.yml         # PostgreSQL + backend + frontend services
├── .env.example               # Environment variable template
└── README.md
```

---

## Local Setup

### Prerequisites

- Node.js 18 or newer
- Python 3.11 or newer
- PostgreSQL 15 or newer (or use Docker Compose)

### Backend

```bash
cd backend

python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API runs at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

To rebuild the simulated history (e.g. after schema changes):

```bash
python -m app.scripts.seed --reset-demo
```

### Environment variables (backend)

Copy `.env.example` to `backend/.env` and set:

```text
DATABASE_URL=postgresql+asyncpg://tiara:tiara_password@localhost:5432/tiara_db
JWT_SECRET_KEY=<a-long-random-secret-minimum-32-chars>
LLM_API_KEY=<your-gemini-api-key>        # required for AI-generated guidance answers
LLM_PROVIDER=gemini
MEDIA_ENCRYPTION_KEY=<fernet-key>        # required; generate with command below
FRONTEND_URL=http://localhost:3000
DEMO_MODE=True
```

Generate a Fernet key for `MEDIA_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Warning:** if `MEDIA_ENCRYPTION_KEY` is lost, all encrypted recordings (`.webm.enc` files) become permanently unreadable. Store the key securely and keep a backup copy.

The faster-whisper model (`base`, ~145 MB) is downloaded automatically on first use. No manual download step is needed.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`. Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in `frontend/.env.local` if the backend is not on the default port.

### Docker Compose

```bash
# Windows PowerShell
$env:JWT_SECRET_KEY="<your-secret>"; docker compose up --build

# macOS / Linux
JWT_SECRET_KEY=<your-secret> docker compose up --build
```

Note: `docker-compose.yml` does not pass `MEDIA_ENCRYPTION_KEY` by default. Add it to your `.env` file at the repository root before building if you need encrypted audio storage.

---

## Deployment

Demo berjalan secara lokal. Panduan deployment akan ditambahkan setelah backend dihosting.

---

## AI Pipeline (Check-in Analysis)

After a check-in session is finished via `POST /elderly/checkin/{session_id}/finish`, TIARA processes all recorded audio through these steps:

1. **Decryption** - `.webm.enc` files are decrypted in memory using Fernet.
2. **Transcription** - each answer's audio is transcribed with faster-whisper (`base` model, Indonesian, CPU int8, word timestamps, VAD filter).
3. **Voice feature extraction** - per answer: words per minute (from word timestamps), inter-word pauses >= 0.5 s, hesitation words (`eh`, `ehm`, `hmm`, `anu`, `apa ya`, etc.), consecutive word repetitions, and response delay (timestamp of first word). Features are aggregated across all answers.
4. **Baseline selection** - if the patient has >= 3 prior real sessions, the median of the last 14 sessions is used as personal baseline. Otherwise, general reference values are used (100 wpm, 0.8 s pause, 2.0 hesitations/min, 2.0 s response delay).
5. **Risk scoring** - score = clamp(1.5 + 7.5 * weighted_deviation, 0, 10). Weights: speech rate 0.3, pause 0.3, response delay 0.3, hesitation 0.1. Level: Rendah (< 4), Sedang (4-6.9), Tinggi (>= 7).
6. **Alerts** - a WARNING alert is created if the score is Tinggi; an INFO alert is created if fewer than 5 words were detected.

**What is not in the real pipeline:** there is no librosa audio analysis, no OpenCV facial analysis, and no language analysis (orientation, memory, coherence) in real sessions. The `language_component`, `facial_component`, and `memory_component` fields in `risk_scores` are null for all real check-in sessions. These fields are populated only in simulated demo data.

All results are informational indicators only, not diagnoses.

---

## Seed Commands

```bash
# From the backend/ directory:

# Normal seed (idempotent - safe to run multiple times)
python -m app.scripts.seed

# Reset and rebuild all simulated history
python -m app.scripts.seed --reset-demo
```

---

## RAG Evaluation Command

```bash
# From the backend/ directory:
python -m app.scripts.evaluasi_rag docs/evaluasi-rag/pertanyaan_uji_dokumen.csv
python -m app.scripts.evaluasi_rag docs/evaluasi-rag/pertanyaan_uji_awam.csv
```

Results are saved to `evaluasi_rag_hasil.csv` in the current directory.

---

## Documentation

Additional project documentation is in [`docs/`](docs/):

- [Product requirements](docs/01-product-requirements.md)
- [MVP scope](docs/02-mvp-scope.md)
- [System architecture](docs/03-system-architecture.md)
- [Database design](docs/04-database-design.md)
- [API specification](docs/05-api-specification.md)
- [AI pipeline](docs/06-ai-pipeline.md)
- [Security and privacy](docs/07-security-and-privacy.md)
- [Development roadmap](docs/08-development-roadmap.md)
- [Demo script](docs/09-demo-script.md)
- [RAG evaluation files](docs/evaluasi-rag/)

---

## Known Limitations

- Dashboard data for the demo patient (Nenek Ladya) is a mix of 60 days of simulated history and any real sessions from voice check-ins. There is no visual separation between simulated and real data in the chart.
- Voice scores are informational indicators based on speech pattern deviation. They have not been clinically validated and are not a substitute for professional assessment.
- faster-whisper frequently removes hesitation words (`eh`, `hmm`, etc.) during transcription, so hesitation counts tend to be underestimated.
- Transcript text in the `transcripts` table is stored unencrypted in the database.
- The mood journal is saved to the database but is not yet shown to caregivers or healthcare workers.
- Summary cards on the caregiver dashboard (Memory Consistency, Response Delay, Speech Hesitation) may show static or simulated values for sessions without a full real analysis. Verify visually during demo.
- AI analysis quality depends on microphone quality and ambient noise.
- Dementia Guidance AI responses are only as current as the loaded documents.
- RAG evaluation measures retrieval accuracy only; faithfulness of generated answers has not been evaluated.
- The plain-language RAG evaluation sample is small (10 questions); results are indicative only.
- TIARA must not be used as a substitute for professional medical evaluation.

---

## Meet the Team

<table>
<tr>
<td align="center" width="50%">
<img src="https://drive.google.com/uc?export=view&id=17JzgCaF45gCTXnlIglXVKpq05sTQq5Vx" width="144" height="180"/>
<br/>
<a href="https://github.com/Arieslana01">
<b>Muhammad Aris Maulana</b>
</a>
<br/>
<i>Universitas Diponegoro</i>
</td>
<td align="center" width="50%">
<img src="https://drive.google.com/uc?export=view&id=1rPzNkUuXtFebZFcrLa7c-ZtZlSnxa0jX" width="144" height="180"/>
<br/>
<a href="https://github.com/narazla">
<b>Nazla Azzahra Hermana</b>
</a>
<br/>
<i>Universitas Diponegoro</i>
</td>
</tr>
</table>

---

Built for **IBM SkillsBuild University Education National Hackathon 2026**
**Hacktiv8 x IBM x Komdigi**

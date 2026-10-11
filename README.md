# TIARA — AI Cognitive Care Platform

> **Medical disclaimer:** TIARA is not a medical diagnosis tool. It provides informational cognitive trend monitoring and caregiver support only, and does not replace professional clinical assessment. Always consult a qualified healthcare professional for medical advice.

---

## Ringkasan (Indonesian)

TIARA (Thinking, Interaction, And Recall Assistant) adalah platform perawatan kognitif berbasis AI yang membantu keluarga mendeteksi perubahan kognitif dini pada lansia melalui sesi check-in harian berbasis video dan audio. Platform ini menyediakan dashboard terlindungi PIN untuk caregiver berisi tren risiko, peringatan, dan rekomendasi perawatan. TIARA juga dilengkapi Dementia Guidance AI — chatbot yang menjawab pertanyaan caregiver berdasarkan dokumen PNPK Tata Laksana Demensia dan panduan caregiver Kemenkes, kini diintegrasikan dengan IBM Bob melalui Langflow MCP. TIARA bukan alat diagnosis medis; seluruh hasil bersifat indikatif dan informatif.

---

## Overview

TIARA addresses a gap in early cognitive care for older adults and their families. Informal caregivers often lack timely, evidence-based guidance; clinical teams lack longitudinal data between appointments; and the older adult themselves needs a gentle, non-clinical daily interaction rather than a medical test.

TIARA brings three experiences together in one platform:

- **Older adults** complete a gentle daily check-in through their device camera and microphone, guided by AI questions.
- **Caregivers** access a PIN-protected dashboard that aggregates cognitive risk trends, smart alerts, AI care recommendations, and a dementia guidance chat.
- **Healthcare workers** monitor patients, review longitudinal session data, and access monthly reports.

---

## Core User Flows

```text
Older adult:
  Login → Home → Daily check-in → Video/audio capture → Supportive result page

Caregiver:
  Login → Caregiver PIN → Dashboard → Alerts → Recommendations → Dementia Guidance AI → Reports

Healthcare worker:
  Login → Patient monitoring → Session history → Longitudinal trends → Monthly reports
```

---

## Features

- **Daily video/audio check-in** — AI-guided spoken questions with consent-based camera and microphone capture.
- **AI analysis pipeline** — Transcription (faster-whisper), voice feature extraction (librosa), language analysis, basic facial analysis (OpenCV), and composite cognitive risk scoring.
- **Caregiver dashboard** — Cognitive risk trend charts (30-day), patient summary, smart alerts feed, AI care recommendations grouped by category, and monthly reports.
- **Dementia Guidance AI** — Answers caregiver questions by retrieving relevant passages from validated Indonesian medical documents (PNPK Tata Laksana Demensia, Kemenkes caregiver guide) using a FAISS vector index and multilingual-e5-large embeddings, then synthesizing a response with Gemini. Responds in the language of the question.
- **Role-based access** — Separate flows and protected routes for older adults, caregivers, and healthcare workers.
- **Caregiver PIN protection** — A secondary access step required to enter the caregiver dashboard, independent of the main login session.

---

## IBM Bob + Langflow Integration

TIARA's Dementia Guidance capability is also exposed as an MCP (Model Context Protocol) tool through Langflow, making it callable directly from IBM Bob.

### How it works

1. **Langflow agent** — A flow named `TIARA` is configured in Langflow Desktop with a single tool: `answer_from_dementia_guidelines`. The agent is loaded with the PNPK Tata Laksana Demensia and the Kemenkes caregiver guide as document context.
2. **MCP server** — Langflow exposes the project as an MCP server at:
   ```
   http://localhost:7860/api/v1/mcp/project/<project-id>/streamable
   ```
3. **Bob as MCP client** — IBM Bob connects to this MCP server via `mcp-proxy` (configured in `~/.bob/settings/mcp.json`). The tool `answer_from_dementia_guidelines` then appears in Bob's tool list and can be invoked in any Bob conversation.

### Guardrails

- The agent answers only from the loaded document context. If a question falls outside the documents, it acknowledges the gap rather than guessing.
- It does not provide medical diagnoses or specific medication dosages.
- It always directs the caregiver to a healthcare professional when the question requires clinical judgment.

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

> Replace `<your-project-id>` with the UUID shown in Langflow → your project → MCP Server tab.

---

## Responsible AI

| Principle | Implementation |
|---|---|
| Informed consent | Camera and microphone access requires explicit per-session consent |
| Caregiver privacy | Dashboard requires a separate PIN; JWT tokens expire |
| Role separation | Elderly, caregiver, and healthcare worker flows are fully separated |
| Medical disclaimer | Shown at every result and in-app guidance screen |
| Evidence-based guidance | RAG retrieves from official Indonesian clinical documents only |
| Human oversight | All AI results are indicators; clinical decisions remain with healthcare professionals |
| No hallucination guardrail | Guidance AI acknowledges when a question is not covered by the source documents |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Framer Motion, Recharts, Radix UI |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2 (async), PostgreSQL 15, Alembic |
| Authentication | JWT (python-jose), bcrypt, caregiver PIN protection |
| AI — media analysis | faster-whisper (transcription), librosa (voice features), OpenCV (video) |
| AI — guidance RAG | FAISS, sentence-transformers (multilingual-e5-large), Google Gemini |
| AI — Bob integration | Langflow MCP server, mcp-proxy, IBM Bob |

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
│   │   ├── routes/            # auth, elderly, caregiver route handlers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── services/          # RAG guidance service, auth service
│   │   │   └── rag_data/      # Pre-built FAISS index and document chunks
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── core/              # Config, security, dependencies
│   │   └── scripts/           # Database seed script
│   └── alembic/               # Database migrations
├── docs/                      # Product, architecture, API, AI, and security docs
├── docker-compose.yml         # PostgreSQL + backend + frontend services
├── .env.example               # Environment variable template
└── README.md
```

---

## Local Setup

### Prerequisites

- Node.js 18 or newer
- Python 3.11 or newer
- PostgreSQL 15 or newer
- Optional: Docker and Docker Compose

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

### Environment variables (backend)

Copy `.env.example` to `backend/.env` and set:

```text
DATABASE_URL=postgresql+asyncpg://tiara:tiara_password@localhost:5432/tiara_db
JWT_SECRET_KEY=<a-long-random-secret>
GEMINI_API_KEY=<your-gemini-api-key>        # required for AI-generated guidance answers
ENABLE_LOCAL_RAG=true                        # set to true to use the FAISS index locally
FRONTEND_URL=http://localhost:3000
```

`ENABLE_LOCAL_RAG=false` disables the local embedding model (suitable for low-memory hosts); the guidance service falls back to Gemini-only responses for documented questions.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:3000`. Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` if the backend is not on the default port.

### Docker Compose

```bash
docker compose up --build
```

Set `JWT_SECRET_KEY` and any optional AI keys as environment variables or in a `.env` file at the repository root before running in production.

### Deployment

- **Backend:** Render or Railway. Set root directory to `backend`. The `Dockerfile` installs dependencies, runs migrations, and starts Uvicorn.
- **Frontend:** Vercel. Set `NEXT_PUBLIC_BACKEND_URL` to your backend service URL.

---

## AI Pipeline (Check-in Analysis)

After a check-in is submitted, TIARA processes the session through these stages:

1. **Transcription** — recorded audio is transcribed with faster-whisper.
2. **Voice feature extraction** — speech rate, pause patterns, and hesitation signals via librosa.
3. **Language analysis** — orientation, memory recall, coherence, and vocabulary indicators.
4. **Video analysis** — basic facial signal extraction with OpenCV when media is available.
5. **Composite risk scoring** — a cognitive risk index is computed and stored.
6. **Alerts and recommendations** — patterns trigger caregiver alerts and grouped care recommendations.

All results are informational indicators only, not diagnoses.

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

---

## Known Limitations

- Several summary cards on the caregiver dashboard (Memory Consistency, Response Delay, Speech Hesitation) show static sample values rather than live computed data.
- AI analysis quality depends on media quality (microphone, camera, ambient noise) and whether the AI services are configured and reachable.
- The local FAISS index (`ENABLE_LOCAL_RAG=true`) requires significant memory; it is disabled by default on hosted plans with limited RAM.
- Dementia Guidance AI responses are only as current as the loaded documents; they do not reflect clinical developments published after the document versions in the index.
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

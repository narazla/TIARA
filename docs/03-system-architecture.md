# 03 - System Architecture

## Architecture Overview

TIARA follows a layered monorepo architecture with clear separation between the frontend, backend API, and AI service layer. The system is Docker-ready and environment-variable-driven.

```
TIARA-IBM/
├── frontend/          # Next.js (App Router) + TypeScript + Tailwind CSS
├── backend/           # FastAPI + Python + PostgreSQL
├── langflow/          # Exported Langflow flow (IBM Bob MCP tool)
├── docs/              # Documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js (App Router) + TypeScript | Routing, SSR, UI framework |
| **Styling** | Tailwind CSS v4 + Radix UI | Design system and components |
| **State/Forms** | React Hook Form + Zod | Form handling and validation |
| **Charts** | Recharts | Dashboard visualizations |
| **Animation** | Framer Motion | Smooth transitions |
| **Backend API** | FastAPI + Python 3.11 | REST API layer |
| **ORM** | SQLAlchemy 2 (async) | Database access layer |
| **Database** | PostgreSQL 15 | Primary data store |
| **Migrations** | Alembic | Database schema versioning |
| **Auth** | JWT (python-jose) + bcrypt | Token-based authentication |
| **Media Upload** | python-multipart | File upload handling |
| **ASGI Server** | Uvicorn | Production ASGI server |
| **STT** | faster-whisper | Speech-to-text transcription |
| **Media Security** | cryptography (Fernet) | Audio file encryption at rest |
| **RAG** | FAISS + multilingual-e5-large + Gemini | In-app guidance AI |
| **Bob MCP** | Langflow + mcp-proxy | IBM Bob integration |
| **Browser Media** | getUserMedia + MediaRecorder | Microphone capture |
| **TTS** | SpeechSynthesisUtterance (Web Speech API) | Spoken AI questions |

---

## Two AI Paths

TIARA has two separate AI paths that must not be confused:

### Path 1: In-App RAG (Caregiver Guidance Chat)

Used when a caregiver types a question in the guidance chat inside the web application.

```
User question
    -> Query expansion (_perluas_pertanyaan)
    -> multilingual-e5-large embedding ("query: " prefix)
    -> FAISS index search (TOP_K=6, index_256token.faiss, 558 chunks)
    -> Gemini generates answer from retrieved context
    -> Answer + source page labels returned
```

Index composition: 396 chunks from PNPK Demensia + 162 chunks from Panduan Caregiver Kemenkes.

Page label logic: PNPK stores pages starting at 0; displayed label = stored index + 1. Caregiver Guide stores pages starting at 1; used as-is.

### Path 2: Langflow MCP (IBM Bob)

Used when a user asks IBM Bob via the `answer_from_dementia_guideline` tool.

```
Bob question -> MCP tool call -> Langflow agent
    -> Full text of both documents inserted into Gemini prompt (no vector search)
    -> Gemini generates answer
    -> Answer returned to Bob
```

Consequence: each call uses the full document text in the prompt (~250k tokens). On Gemini free tier this limits throughput to approximately one question per minute.

Page number difference: in the Langflow path, PNPK page references are corrected via agent instructions; Caregiver Guide references use the printed book page number (e.g. page 14), which differs from the PDF page number (e.g. 24) used in Path 1.

Planned improvement: switching the Langflow path to vector search (Chroma) is planned but not yet implemented.

---

## Request Flow

### Authentication Flow

```
Client -> POST /api/v1/auth/login (email + password)
       -> Backend validates credentials (bcrypt)
       -> JWT access token generated (type: "access", 60 min TTL)
       -> Token returned to client
       -> Client stores token
       -> Subsequent requests: Authorization: Bearer <token>
       -> Backend checks token type == "access" in dependency
```

### Daily Check-in Flow (Real Session)

```
Elderly user
    |
    +-- /elderly/home -> clicks "Daily Check-In"
    |
    +-- /elderly/check-in
            |
            +-- Browser: navigator.mediaDevices.getUserMedia({video: true, audio: true})
            |   Video used for local preview only; NOT recorded, NOT sent to backend
            +-- Browser: MediaRecorder per question (audio stream only)
            +-- Browser: SpeechSynthesisUtterance speaks question
            |
            +-- POST /api/v1/elderly/checkin/start {consent: true}
            |   -> Creates CheckinSession, returns session_id
            |
            +-- POST /api/v1/elderly/checkin/{id}/answer (per question)
            |   -> Audio blob uploaded, encrypted with Fernet, saved as .webm.enc
            |
            +-- POST /api/v1/elderly/checkin/{id}/finish
                    |
                    +-- Decrypt .webm.enc files in memory
                    +-- faster-whisper transcription per answer
                    +-- Voice feature extraction (WPM, pauses, hesitations, response delay)
                    +-- Feature aggregation across answers
                    +-- Baseline selection (personal median or general reference)
                    +-- Risk score calculation (0-10, weighted deviation)
                    +-- Save Transcript, VoiceAnalysisResult, RiskScore
                    +-- Generate alerts if applicable
                    +-- Return {status, session_id, perlu_perhatian}
```

Note: language analysis, facial analysis, and memory scoring are NULL for all real sessions. These components appear only in simulated demo data.

### Caregiver Dashboard Flow

```
Profile Dropdown -> "Dashboard" -> /caregiver/pin
    |
    +-- POST /api/v1/caregiver/verify-pin (PIN input)
            -> bcrypt verify PIN hash
            -> Return: dashboard_token (JWT, 30 min TTL)
    |
    +-- /caregiver/dashboard (with X-Dashboard-Token header)
            +-- GET /api/v1/caregiver/dashboard -> patient analytics
            +-- GET /api/v1/caregiver/alerts -> generated alerts
            +-- GET /api/v1/caregiver/recommendations -> care recommendations
            +-- POST /api/v1/caregiver/guidance/ask -> RAG guidance answer
            +-- GET /api/v1/caregiver/reports -> monthly reports
```

All caregiver endpoints verify that X-Dashboard-Token is present and belongs to the same user as the JWT. Missing or mismatched token returns 403 with detail "PIN_DIPERLUKAN".

---

## Backend Layer Architecture

```
routes/          <- Thin HTTP handlers (input validation, response shaping)
    |
services/        <- Business logic (orchestration, AI pipeline)
    |
repositories/    <- Data access (SQLAlchemy queries, no business logic)
    |
models/          <- SQLAlchemy ORM models
    |
database/        <- Session management, connection pool
    |
PostgreSQL
```

---

## Frontend Layer Architecture

```
app/             <- Next.js App Router pages (thin page components)
    |
components/      <- UI components (layout, forms, charts, shared)
    |
lib/
  +-- api/       <- Typed API client functions (Axios wrappers)
  +-- auth/      <- Auth context, token management
  +-- hooks/     <- Custom React hooks
  +-- types/     <- TypeScript interfaces and types
  +-- utils/     <- Helper functions
```

---

## Storage Architecture

```
MEDIA_STORAGE_PATH/
+-- {session_id}/
    +-- jawaban_0.webm.enc    # Fernet-encrypted audio, question 0
    +-- jawaban_1.webm.enc    # Fernet-encrypted audio, question 1
    +-- jawaban_2.webm.enc
    +-- jawaban_3.webm.enc
```

Files are decrypted in memory during the `/finish` call. Decrypted bytes are never written back to disk.

---

## Security Architecture

- **Authentication**: JWT access tokens, 60-minute TTL, type field enforced
- **Password hashing**: bcrypt via passlib
- **Caregiver PIN**: bcrypt hashed, dashboard token verified server-side
- **PIN gate header**: X-Dashboard-Token required on all caregiver endpoints; missing or wrong token -> 403 PIN_DIPERLUKAN
- **CORS**: configured for FRONTEND_URL origins only; X-Dashboard-Token is in allowed headers
- **Role checks**: require_role dependency enforced on all protected routes (3 roles: elderly, caregiver, healthcare)
- **Audio encryption**: Fernet at rest (.webm.enc); key from MEDIA_ENCRYPTION_KEY env var
- **Environment secrets**: never committed; loaded from .env
- **Transcript storage**: transcript text is NOT encrypted in the database

---

## Deployment Architecture (Docker)

```yaml
# docker-compose.yml
services:
  postgres:    # PostgreSQL 15 on port 5432
  backend:     # FastAPI on port 8000 (alembic upgrade + seed + uvicorn)
  frontend:    # Next.js on port 3000
```

Docker Compose is provided for local development and testing. A production hosting guide will be added once the backend is deployed to a hosting provider.

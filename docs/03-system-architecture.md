# 03 — System Architecture

## Architecture Overview

TIARA follows a **layered monorepo architecture** with a clear separation between the frontend, backend API, and AI service layer. The system is designed to be Docker-ready and environment-variable-driven.

```
tiara/
├── frontend/          # Next.js 14 + TypeScript + Tailwind CSS
├── backend/           # FastAPI + Python + PostgreSQL
├── docs/              # Documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | Routing, SSR, UI framework |
| **Styling** | Tailwind CSS + shadcn/ui | Design system and components |
| **State/Forms** | React Hook Form + Zod | Form handling and validation |
| **Charts** | Recharts | Dashboard visualizations |
| **Animation** | Framer Motion | Smooth transitions |
| **Icons** | Lucide React | Icon library |
| **Backend API** | FastAPI + Python | REST API layer |
| **ORM** | SQLAlchemy + SQLModel | Database access layer |
| **Database** | PostgreSQL | Primary data store |
| **Migrations** | Alembic | Database schema versioning |
| **Auth** | JWT + Passlib (bcrypt) | Token-based authentication |
| **Media Upload** | python-multipart | File upload handling |
| **ASGI Server** | Uvicorn | Production ASGI server |
| **STT** | faster-whisper / Whisper | Speech-to-text transcription |
| **Audio Analysis** | librosa / pydub | Voice feature extraction |
| **Video Analysis** | OpenCV / MediaPipe | Facial/video processing |
| **LLM** | Pluggable (OpenAI, Anthropic, Gemini, local) | Dementia Guidance AI |
| **Browser Media** | getUserMedia + MediaRecorder | Camera/microphone capture |
| **TTS** | SpeechSynthesisUtterance (Web Speech API) | Spoken AI questions |

---

## Request Flow

### Authentication Flow
```
Client → POST /auth/login (email + password)
       → Backend validates credentials
       → Bcrypt password verification
       → JWT token generated (role embedded)
       → Token returned to client
       → Client stores token (httpOnly cookie or memory)
       → Subsequent requests: Authorization: Bearer <token>
```

### Daily Check-In Flow
```
Elderly User
    │
    ├── /elderly/home → clicks "Daily Check-In"
    │
    ├── /elderly/check-in
    │       │
    │       ├── Browser: navigator.mediaDevices.getUserMedia({video: true, audio: true})
    │       ├── Browser: MediaRecorder starts per question
    │       ├── Browser: SpeechSynthesisUtterance speaks question
    │       ├── User answers → recording saved
    │       ├── Next question → repeat
    │       └── Finish Check-In
    │               │
    │               ├── POST /checkins/start → create session
    │               ├── POST /checkins/{id}/answer → save answer text
    │               ├── POST /checkins/{id}/upload-media → upload audio/video blob
    │               └── POST /checkins/{id}/finish → trigger AI pipeline
    │
    ├── Backend: AI Pipeline (async)
    │       ├── TranscriptionService.transcribe(audio_path)
    │       ├── VoiceAnalysisService.analyze(audio_path, transcript)
    │       ├── LanguageAnalysisService.analyze(transcript, answers)
    │       ├── FacialAnalysisService.analyze(video_path)
    │       ├── RiskScoringService.score(all_analysis_results)
    │       ├── AlertService.generate(risk_score, history)
    │       └── RecommendationService.generate(risk_score, indicators)
    │
    └── /elderly/check-in/result (warm result page)
```

### Caregiver Dashboard Flow
```
Profile Dropdown → "Dashboard" → /caregiver/pin
    │
    ├── POST /caregiver/verify-pin (PIN input)
    │       └── Backend: bcrypt verify PIN hash
    │               └── Return: caregiver_session_token
    │
    └── /caregiver/dashboard (with caregiver_session_token)
            ├── GET /caregiver/dashboard → patient analytics
            ├── GET /caregiver/alerts → generated alerts
            ├── GET /caregiver/recommendations → care plan
            ├── POST /guidance/ask → AI chat response
            └── GET /caregiver/reports → monthly summary
```

---

## Backend Layer Architecture

```
routes/          ← Thin HTTP handlers (input validation, response shaping)
    │
services/        ← Business logic (orchestration, rules, AI pipeline)
    │
repositories/    ← Data access (SQLAlchemy queries, no business logic)
    │
models/          ← SQLAlchemy/SQLModel ORM models
    │
database/        ← Session management, connection pool
    │
PostgreSQL
```

**Principle**: Routes delegate to services. Services delegate to repositories. Repositories speak only to the database. No business logic in routes or repositories.

---

## Frontend Layer Architecture

```
app/             ← Next.js App Router pages (thin page components)
    │
components/      ← UI components (layout, forms, charts, shared)
    │
lib/
  ├── api/       ← Typed API client functions (fetch wrappers)
  ├── auth/      ← Auth context, token management
  ├── hooks/     ← Custom React hooks
  ├── types/     ← TypeScript interfaces and types
  ├── utils/     ← Helper functions
  └── constants/ ← App-wide constants
```

---

## AI Service Layer

All AI services implement a **provider abstraction pattern**:

```python
class BaseTranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        ...

class WhisperProvider(BaseTranscriptionProvider):
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        # faster-whisper implementation
        ...

class FallbackProvider(BaseTranscriptionProvider):
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        # Returns empty transcript with metadata, not fake data
        ...
```

This allows:
- Real Whisper transcription when available
- Clean fallback without fake hardcoded data
- Easy swap of any AI provider via config/environment variables

---

## Storage Architecture

```
MEDIA_STORAGE_PATH/
└── sessions/
    └── {session_id}/
        ├── question_{n}_audio.webm
        ├── question_{n}_video.webm
        └── session_video.webm
```

For production: replace local filesystem with S3-compatible object storage by swapping `media_service.py` storage provider.

---

## Security Architecture

- **Authentication**: JWT tokens with expiry
- **Password hashing**: bcrypt via Passlib
- **Caregiver PIN**: bcrypt hashed in database
- **CORS**: Configured for known frontend origin only
- **Role checks**: Middleware enforced on all protected routes
- **Media files**: Stored outside web root, served via authenticated endpoints
- **Environment secrets**: Never committed; loaded from `.env`

---

## Deployment Architecture (Docker)

```yaml
# docker-compose.yml
services:
  frontend:     # Next.js on port 3000
  backend:      # FastAPI on port 8000
  postgres:     # PostgreSQL on port 5432
```

Each service has its own `Dockerfile`. Environment configured via `.env` file at root level.

---

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                          BROWSER                             │
│  Next.js Frontend                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │ Elderly  │  │Caregiver │  │   Healthcare             │  │
│  │   UI     │  │   UI     │  │      UI                  │  │
│  └──────────┘  └──────────┘  └──────────────────────────┘  │
│       │              │                    │                  │
│  getUserMedia   Recharts Charts     Patient List            │
│  MediaRecorder  Alerts/Reports      Session View            │
│  SpeechSynth    Guidance Chat                               │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS / REST API
                       │ Authorization: Bearer JWT
┌──────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │   Routes   │  │  Services   │  │    Repositories      │  │
│  │ (thin)     │→ │ (logic)     │→ │    (data access)     │  │
│  └────────────┘  └─────────────┘  └──────────────────────┘  │
│                        │                    │                │
│                   AI Pipeline          SQLAlchemy            │
│               ┌────────┴────────┐           │               │
│           Whisper/STT      RiskScoring       ▼               │
│           AudioAnalysis    Alerts      PostgreSQL            │
│           FaceDetection    Recos                             │
└──────────────────────────────────────────────────────────────┘
```

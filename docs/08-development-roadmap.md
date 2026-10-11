# 08 — Development Roadmap

## Overview

TIARA's development is broken into 10 phases. Each phase builds on the previous and delivers a testable increment. The MVP target is completion through Phase 9.

---

## Phase 1: Project Setup and Documentation ✅

**Goal**: Establish the repository structure, tooling, and documentation foundation.

### Tasks
- [x] Create monorepo at `tiara/`
- [x] Create `docs/` folder with all 9 documentation files
- [x] Create `README.md` at root with full setup instructions
- [x] Create `.env.example` with all required variables
- [x] Create `docker-compose.yml` skeleton
- [x] Initialize `frontend/` with Next.js + TypeScript + Tailwind CSS + shadcn/ui
- [x] Initialize `backend/` with FastAPI project structure
- [x] Configure ESLint, Prettier for frontend
- [x] Configure Black, isort, Ruff for backend
- [x] Create `backend/requirements.txt`

**Deliverable**: Running `npm run dev` in frontend shows Next.js landing page skeleton. Running `uvicorn` in backend shows FastAPI health check.

---

## Phase 2: Authentication and Role Management ✅

**Goal**: Real working authentication with JWT, bcrypt, and role-based access.

### Backend
- [x] Define `User` SQLAlchemy model
- [x] Create Alembic initial migration
- [x] Implement `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
- [x] Implement JWT token generation and verification
- [x] Implement bcrypt password hashing
- [x] Implement role-based middleware dependencies
- [x] Create seed script with 3 demo users

### Frontend
- [x] Login page (`/login`)
- [x] Register page (`/register`)
- [x] Auth context with user state
- [x] Protected route wrapper
- [x] Role-based redirect after login (elderly → `/elderly/home`, caregiver → `/caregiver/pin`, healthcare → `/healthcare/dashboard`)
- [x] Token storage and auth header injection
- [x] Logout functionality

**Deliverable**: Login with demo credentials works. Role-based redirect works. Protected pages redirect unauthenticated users.

---

## Phase 3: Elderly Flow

**Goal**: Elderly home page and profile with real data from backend.

### Backend
- [x] Define `Patient` model and migration
- [x] `GET /elderly/home` endpoint with today's check-in status
- [x] `GET /elderly/profile` endpoint

### Frontend
- [x] Elderly home page (`/elderly/home`) with personalized greeting
- [x] Check-in status indicator
- [x] Profile dropdown with Dashboard and Logout
- [x] TIARA Companion page (`/elderly/companion`) with 4 activity cards
- [x] Companion sub-pages (story time, memory game, mood check, family memories)

**Deliverable**: Full elderly home experience works with real user data.

---

## Phase 4: Daily Video/Audio Check-In (Frontend)

**Goal**: Real browser-based check-in with camera, microphone, and spoken questions.

### Frontend
- [x] Check-in page (`/elderly/check-in`)
- [x] `getUserMedia` camera + microphone setup
- [x] Live video preview component
- [x] `MediaRecorder` per-question audio recording
- [x] `SpeechSynthesisUtterance` spoken questions
- [x] Question panel with category, progress, status indicators
- [x] All 8 questions with 4 categories
- [x] Per-question recording, stop, and next flow
- [x] Finish check-in and upload logic
- [x] Camera/microphone denied error handling with retry
- [x] Check-in result page (`/elderly/check-in/result`) — warm, reassuring, no clinical data

**Deliverable**: Full check-in flow works in browser. Recording captured, questions spoken, user flow complete.

---

## Phase 5: Backend Check-In API and Database Persistence

**Goal**: All check-in data stored in database with complete session lifecycle.

### Backend
- [x] Define all check-in models: `CheckinSession`, `CheckinAnswer`, `MediaFile`, `CheckinQuestion`
- [x] Alembic migrations for check-in tables
- [x] Seed initial question bank (8 questions, 4 categories)
- [x] `POST /checkins/start` — create session, return questions
- [x] `GET /checkins/current` — active session lookup
- [x] `POST /checkins/{id}/answer` — save answer record
- [x] `POST /checkins/{id}/upload-media` — save uploaded file metadata
- [x] `POST /checkins/{id}/finish` — complete session, queue pipeline
- [x] `GET /checkins/{id}` — session detail (role-filtered)
- [x] `GET /checkins/history` — paginated session history

**Deliverable**: Complete check-in end-to-end: frontend captures → uploads → backend persists. Session status correct.

---

## Phase 6: AI Transcription and Analysis Pipeline

**Goal**: Real AI analysis pipeline processes sessions and stores results.

### Backend
- [x] `TranscriptionService` with Whisper + fallback provider
- [x] `VoiceAnalysisService` with librosa + metadata fallback
- [x] `LanguageAnalysisService` with rule-based scoring
- [x] `FacialAnalysisService` with OpenCV + metadata fallback
- [x] `RiskScoringService` with composite formula
- [x] `AlertService` with trigger rules
- [x] `RecommendationService` with risk-based rules
- [x] `AIPipelineService` orchestrating all services
- [x] Background task integration in finish endpoint
- [x] All results stored in respective tables

**Deliverable**: After finishing check-in, pipeline runs, all tables populated, risk score generated.

---

## Phase 7: Caregiver PIN and Dashboard

**Goal**: Working caregiver dashboard with real check-in analysis data.

### Backend
- [x] `CaregiverPin` model with bcrypt hashing
- [x] `POST /caregiver/verify-pin` with lockout logic
- [x] `GET /caregiver/dashboard` with patient analytics
- [x] `GET /caregiver/alerts` with generated alerts
- [x] `GET /caregiver/recommendations`
- [x] Seed caregiver PIN (123456 hashed)
- [x] Seed caregiver-patient link

### Frontend
- [x] PIN page (`/caregiver/pin`) with 6-digit input
- [x] Caregiver dashboard (`/caregiver/dashboard`) with Recharts trend chart
- [x] Caregiver sidebar navigation
- [x] Alerts page (`/caregiver/alerts`)
- [x] Recommendations page (`/caregiver/recommendations`)
- [x] Risk score color coding (green/gold/red)
- [x] Dashboard token verification on protected routes

**Deliverable**: PIN verification works. Dashboard shows real data from completed check-in.

---

## Phase 8: Guidance AI, Recommendations, Reports

**Goal**: Working guidance chatbot and report generation.

### Backend
- [x] `GuidanceService` with rule-based + LLM provider abstraction
- [x] `POST /guidance/ask` endpoint
- [x] `GET /guidance/history` endpoint
- [x] `ReportService` generating monthly reports
- [x] `POST /reports/generate` endpoint
- [x] `GET /reports/{id}` endpoint
- [x] PDF generation (WeasyPrint or print-friendly HTML)

### Frontend
- [x] Guidance chat page (`/caregiver/guidance`) with chat UI
- [x] Suggested questions
- [x] Medical disclaimer
- [x] Reports page (`/caregiver/reports`)
- [x] Download PDF / print button

**Deliverable**: Caregiver can chat with guidance AI. Reports generated from real session data.

---

## Phase 9: Healthcare Worker Dashboard

**Goal**: Professional dashboard for healthcare workers.

### Backend
- [x] `GET /healthcare/dashboard`
- [x] `GET /healthcare/patients` with risk filter
- [x] `GET /healthcare/patients/{id}`
- [x] Healthcare-patient link seed data

### Frontend
- [x] Healthcare dashboard (`/healthcare/dashboard`)
- [x] Patient list with risk badges
- [x] Patient detail view
- [x] Longitudinal trend chart per patient
- [x] Report access

**Deliverable**: Healthcare worker can view all linked patients with full session data.

---

## Phase 10: Testing, Polish, README, Deployment Readiness

**Goal**: Production-ready quality.

### Testing
- [ ] Backend: pytest tests for auth, PIN, check-in, risk scoring, recommendations
- [ ] Frontend: Playwright or Cypress E2E for critical paths

### Polish
- [ ] Loading states on all async operations
- [ ] Error boundaries on all pages
- [ ] Empty states for no data conditions
- [ ] Mobile responsiveness audit
- [ ] Accessibility audit (keyboard nav, contrast, font sizes)

### Deployment
- [ ] `Dockerfile` for frontend
- [ ] `Dockerfile` for backend
- [ ] `docker-compose.yml` wiring
- [ ] Production `.env` template
- [ ] Alembic migration applied in Docker entrypoint
- [ ] Seed script run on first startup

**Deliverable**: `docker-compose up` brings up entire system. All demo flows work.

---

## Timeline Estimate (Solo Developer)

| Phase | Estimated Time |
|---|---|
| Phase 1 + 2 | 2-3 days |
| Phase 3 | 1 day |
| Phase 4 | 2 days |
| Phase 5 | 2 days |
| Phase 6 | 3 days |
| Phase 7 | 2 days |
| Phase 8 | 2 days |
| Phase 9 | 1 day |
| Phase 10 | 2 days |
| **Total** | **~17-18 days** |

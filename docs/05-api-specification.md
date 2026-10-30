# 05 - API Specification

## Base URL

```
http://localhost:8000/api/v1
```

Interactive docs: `http://localhost:8000/docs` (Swagger UI), `http://localhost:8000/redoc`

---

## Authentication

All protected endpoints require:

```
Authorization: Bearer <access_token>
```

The access token must be of type `"access"` (checked server-side). A token of any other type returns 401.

Caregiver dashboard endpoints additionally require:

```
X-Dashboard-Token: <dashboard_token>
```

If this header is missing, expired, or belongs to a different user, the response is:

```json
HTTP 403
{"detail": "PIN_DIPERLUKAN"}
```

The frontend interprets `PIN_DIPERLUKAN` as a redirect signal to `/caregiver/pin`.

---

## Error Response Format

```json
{
  "detail": "Human-readable error message or error code"
}
```

---

## Authentication Endpoints

### `POST /auth/register`

Register a new user account.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "Nama Lengkap",
  "role": "elderly"
}
```

Valid roles: `"elderly"`, `"caregiver"`, `"healthcare"`.

**Response 201:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Nama Lengkap",
  "role": "elderly"
}
```

---

### `POST /auth/login`

Login and receive an access token.

**Request body:**
```json
{
  "email": "elderly@tiara.app",
  "password": "Lansia_123"
}
```

**Response 200:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### `GET /auth/me`

Get the current authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "id": "uuid",
  "email": "elderly@tiara.app",
  "full_name": "Nenek Ladya",
  "role": "elderly",
  "is_active": true
}
```

---

## Elderly Check-in Endpoints

All endpoints under `/elderly/checkin/*` require role `elderly`.

### `POST /elderly/checkin/start`

Start a new check-in session. Any prior in-progress session for this user is marked abandoned.

**Request body:**
```json
{"consent": true}
```

`consent` must be `true`; `false` returns 400.

**Response 201:**
```json
{"session_id": "uuid"}
```

---

### `POST /elderly/checkin/{session_id}/answer`

Upload audio recording for one question. Accepts multipart/form-data.

**Form fields:**
- `question_order` (int): the `order_index` of the question being answered
- `audio` (file): WebM audio blob; minimum 1000 bytes, maximum 15 MB

The file is encrypted with Fernet and saved as `jawaban_{order}.webm.enc`.

**Response 201:**
```json
{"answer_id": "uuid"}
```

If `MEDIA_ENCRYPTION_KEY` is not set, returns 503.

Uploading for the same `question_order` again replaces the previous file.

---

### `POST /elderly/checkin/{session_id}/finish`

Process all recorded answers for this session: decrypt, transcribe, score, and save results.

**Response 200 (normal completion):**
```json
{
  "status": "selesai",
  "session_id": "uuid",
  "perlu_perhatian": false
}
```

`perlu_perhatian: true` means a WARNING alert was created (score level Tinggi).

**Response 200 (insufficient speech):**
```json
{
  "status": "tidak_ada_suara",
  "session_id": "uuid"
}
```

Returned when fewer than 5 words were detected across all answers. An INFO alert "Check-in hari ini tidak terekam" is created for the caregiver.

**Response 409:** session is already being processed.
**Response 503:** faster-whisper library not installed.

---

## Caregiver Endpoints

All endpoints under `/caregiver/*` require role `caregiver` AND a valid `X-Dashboard-Token` header (unless noted).

### `POST /caregiver/verify-pin`

Verify caregiver PIN and receive a dashboard token.

**Headers:** `Authorization: Bearer <token>` (role caregiver; no X-Dashboard-Token needed)

**Request body:**
```json
{"pin": "123456"}
```

**Response 200:**
```json
{
  "dashboard_token": "<dashboard-jwt>",
  "token_type": "bearer"
}
```

Wrong PIN: 401. After 5 consecutive wrong attempts the account is locked for 15 minutes: 429, with the message in `detail`.

---

### `GET /caregiver/dashboard`

**Headers:** `Authorization: Bearer <token>`, `X-Dashboard-Token: <dashboard-token>`

Returns patient analytics for the caregiver's linked patient(s): risk trend, latest session summary, and patient profile.

---

### `GET /caregiver/alerts`

**Headers:** `Authorization: Bearer <token>`, `X-Dashboard-Token: <dashboard-token>`

Returns list of alerts for the caregiver's patient(s), newest first.

Alert severity values: `"info"`, `"warning"`, `"critical"`.

---

### `GET /caregiver/recommendations`

**Headers:** `Authorization: Bearer <token>`, `X-Dashboard-Token: <dashboard-token>`

Returns care recommendations grouped by category.

---

### `POST /caregiver/guidance/ask`

**Headers:** `Authorization: Bearer <token>`, `X-Dashboard-Token: <dashboard-token>`

Ask the RAG guidance AI a question.

**Request body:**
```json
{"question": "Bagaimana menangani lansia yang gelisah?"}
```

**Response 200:**
```json
{
  "answer": "...",
  "sources": ["PNPK Demensia hal 87", "Panduan Caregiver Kemenkes hal 23"]
}
```

If `LLM_API_KEY` is not configured, returns a message indicating the AI service is not available but includes retrieved sources.

---

### `GET /caregiver/reports`

**Headers:** `Authorization: Bearer <token>`, `X-Dashboard-Token: <dashboard-token>`

Returns list of monthly reports for the patient.

---

## Healthcare Worker Endpoints

All endpoints under `/healthcare/*` require role `healthcare`.

### `GET /healthcare/dashboard`

Returns overview of all patients linked to this healthcare worker.

---

### `GET /healthcare/patients`

Returns paginated patient list with latest risk level and session count.

---

### `GET /healthcare/patients/{patient_id}`

Returns full session history, longitudinal trend, and analysis details for one patient.

---

## Notes on Endpoint Paths

The legacy docs described endpoints like `/checkins/start` and `/guidance/ask` at the top level. The actual routes registered in `backend/app/main.py` are prefixed with `/api/v1` and the check-in router uses prefix `/elderly/checkin`. The caregiver guidance endpoint path depends on the caregiver router implementation; verify against `http://localhost:8000/docs` for the exact paths in the running application.

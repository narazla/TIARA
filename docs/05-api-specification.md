# 05 — API Specification

## Base URL

```
Development:  http://localhost:8000/api/v1
Production:   https://api.tiara.app/api/v1
```

## Authentication

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

Tokens are JWTs signed with `JWT_SECRET_KEY`. They include `user_id`, `role`, and `exp`.

---

## Error Response Format

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE_CONSTANT"
}
```

Common error codes: `INVALID_CREDENTIALS`, `TOKEN_EXPIRED`, `UNAUTHORIZED`, `NOT_FOUND`, `VALIDATION_ERROR`, `FORBIDDEN`

---

## Authentication Endpoints

### `POST /auth/register`
Register a new user account.

**Auth required**: No

**Request body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Nenek Ladya",
  "role": "elderly"
}
```

**Response** `201`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Nenek Ladya",
  "role": "elderly",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors**: `400` (email already exists), `422` (validation error)

---

### `POST /auth/login`
Authenticate and receive JWT token.

**Auth required**: No

**Request body**:
```json
{
  "email": "elderly@tiara.app",
  "password": "password123"
}
```

**Response** `200`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "elderly@tiara.app",
    "full_name": "Nenek Ladya",
    "role": "elderly"
  }
}
```

**Errors**: `401` (invalid credentials), `403` (account inactive)

---

### `GET /auth/me`
Get the current authenticated user's profile.

**Auth required**: Yes

**Response** `200`:
```json
{
  "id": "uuid",
  "email": "elderly@tiara.app",
  "full_name": "Nenek Ladya",
  "role": "elderly",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors**: `401` (missing/invalid token)

---

### `POST /auth/logout`
Invalidate the current session (client-side token removal; optionally server-side blacklist).

**Auth required**: Yes

**Response** `200`:
```json
{ "message": "Logged out successfully" }
```

---

## Elderly Endpoints

### `GET /elderly/home`
Get elderly home page data including today's check-in status.

**Auth required**: Yes (role: elderly)

**Response** `200`:
```json
{
  "user": {
    "full_name": "Nenek Ladya",
    "greeting": "Good morning"
  },
  "todays_checkin": {
    "completed": false,
    "session_id": null,
    "completed_at": null
  },
  "streak_days": 3
}
```

---

### `GET /elderly/profile`
Get elderly user profile information.

**Auth required**: Yes (role: elderly)

**Response** `200`:
```json
{
  "id": "uuid",
  "full_name": "Nenek Ladya",
  "email": "elderly@tiara.app",
  "date_of_birth": "1955-03-15",
  "gender": "F"
}
```

---

## Daily Check-In Endpoints

### `POST /checkins/start`
Start a new check-in session.

**Auth required**: Yes (role: elderly)

**Request body**:
```json
{
  "device_info": "Chrome/120 on macOS"
}
```

**Response** `201`:
```json
{
  "session_id": "uuid",
  "questions": [
    {
      "id": "uuid",
      "category": "orientation",
      "question_text": "What day is today?",
      "order_index": 0
    }
  ],
  "started_at": "2024-01-01T08:00:00Z"
}
```

**Errors**: `409` (session already in progress today)

---

### `GET /checkins/current`
Get the current in-progress session, if any.

**Auth required**: Yes (role: elderly)

**Response** `200`:
```json
{
  "session_id": "uuid",
  "status": "in_progress",
  "started_at": "2024-01-01T08:00:00Z",
  "answers_submitted": 2
}
```

Returns `null` in `session` field if none active.

---

### `POST /checkins/{session_id}/answer`
Submit a text answer for a question.

**Auth required**: Yes (role: elderly)

**Request body**:
```json
{
  "question_id": "uuid",
  "answer_text": "Today is Monday",
  "response_delay_seconds": 2.3,
  "recording_started_at": "2024-01-01T08:01:05Z",
  "recording_ended_at": "2024-01-01T08:01:12Z"
}
```

**Response** `201`:
```json
{
  "answer_id": "uuid",
  "session_id": "uuid",
  "question_id": "uuid"
}
```

---

### `POST /checkins/{session_id}/upload-media`
Upload audio or video recording for a question.

**Auth required**: Yes (role: elderly)

**Content-Type**: `multipart/form-data`

**Form fields**:
- `file`: binary audio/video file (webm, mp4, etc.)
- `file_type`: `audio` | `video` | `combined`
- `answer_id`: (optional) UUID of associated answer
- `duration_seconds`: float

**Response** `201`:
```json
{
  "media_file_id": "uuid",
  "file_path": "sessions/uuid/question_0_audio.webm",
  "uploaded_at": "2024-01-01T08:01:20Z"
}
```

---

### `POST /checkins/{session_id}/finish`
Complete the check-in session and trigger AI pipeline.

**Auth required**: Yes (role: elderly)

**Request body**:
```json
{
  "total_duration_seconds": 145.2
}
```

**Response** `200`:
```json
{
  "session_id": "uuid",
  "status": "completed",
  "processing_status": "pending",
  "message": "Check-in completed. Processing your session...",
  "result_available_at": "2024-01-01T08:05:00Z"
}
```

---

### `GET /checkins/{session_id}`
Get full session details including analysis results.

**Auth required**: Yes (elderly or linked caregiver/healthcare)

**Response** `200`:
```json
{
  "session_id": "uuid",
  "status": "completed",
  "processing_status": "completed",
  "started_at": "...",
  "completed_at": "...",
  "answers": [...],
  "risk_score": {
    "risk_score": 42,
    "risk_level": "medium",
    "summary": "...",
    "main_indicators": [...]
  },
  "voice_analysis": {...},
  "language_analysis": {...},
  "facial_analysis": {...}
}
```

**Note**: When accessed by elderly role, `risk_score`, `voice_analysis`, `language_analysis`, `facial_analysis` fields are omitted.

---

### `GET /checkins/history`
Get check-in session history for current user.

**Auth required**: Yes

**Query params**: `page=1&per_page=20&status=completed`

**Response** `200`:
```json
{
  "total": 15,
  "sessions": [
    {
      "session_id": "uuid",
      "status": "completed",
      "started_at": "...",
      "completed_at": "...",
      "risk_level": "low"
    }
  ]
}
```

---

## Caregiver Endpoints

### `POST /caregiver/verify-pin`
Verify caregiver PIN and issue dashboard access.

**Auth required**: Yes (role: caregiver)

**Request body**:
```json
{
  "pin": "123456"
}
```

**Response** `200`:
```json
{
  "verified": true,
  "dashboard_token": "short-lived-token",
  "expires_in": 3600
}
```

**Errors**: `401` (wrong PIN), `429` (too many attempts)

---

### `GET /caregiver/dashboard`
Get caregiver dashboard analytics for linked patient(s).

**Auth required**: Yes (role: caregiver + PIN verified)

**Response** `200`:
```json
{
  "patient": {
    "id": "uuid",
    "full_name": "Nenek Ladya",
    "age": 70
  },
  "latest_session": {
    "session_id": "uuid",
    "completed_at": "...",
    "risk_score": 42,
    "risk_level": "medium"
  },
  "trend_data": [
    { "date": "2024-01-01", "risk_score": 38, "risk_level": "low" },
    { "date": "2024-01-02", "risk_score": 42, "risk_level": "medium" }
  ],
  "memory_consistency": 74.5,
  "avg_response_delay": 3.2,
  "speech_hesitation_rate": 0.08,
  "unread_alerts": 2
}
```

---

### `GET /caregiver/alerts`
Get all alerts for the linked patient.

**Auth required**: Yes (role: caregiver + PIN verified)

**Query params**: `is_read=false&severity=warning`

**Response** `200`:
```json
{
  "total": 3,
  "alerts": [
    {
      "id": "uuid",
      "severity": "warning",
      "title": "Memory recall score decreased",
      "description": "Memory recall dropped from 80 to 62 compared to last session.",
      "suggested_action": "Consider simple recall exercises today.",
      "created_at": "...",
      "is_read": false
    }
  ]
}
```

---

### `GET /caregiver/recommendations`
Get active care recommendations.

**Auth required**: Yes (role: caregiver + PIN verified)

**Response** `200`:
```json
{
  "today_plan": [...],
  "cognitive_activities": [...],
  "social_suggestions": [...],
  "medical_notes": [...],
  "when_to_seek_help": [...]
}
```

---

### `GET /caregiver/reports`
Get list of generated reports.

**Auth required**: Yes (role: caregiver + PIN verified)

**Response** `200`:
```json
{
  "reports": [
    {
      "id": "uuid",
      "title": "January 2024 Cognitive Care Summary",
      "report_month": "2024-01-01",
      "checkin_count": 20,
      "avg_risk_score": 41.2,
      "created_at": "..."
    }
  ]
}
```

---

## Guidance AI Endpoints

### `POST /guidance/ask`
Send a message to the Dementia Guidance AI.

**Auth required**: Yes (role: caregiver or healthcare)

**Request body**:
```json
{
  "message": "Why is my mother repeating stories?",
  "session_context_id": null
}
```

**Response** `200`:
```json
{
  "response": "Repeating stories is a common sign of short-term memory changes...",
  "disclaimer": "This guidance is not a medical diagnosis. Please consult a healthcare professional for clinical assessment.",
  "provider": "rule-based",
  "message_id": "uuid"
}
```

---

### `GET /guidance/history`
Get conversation history for the current caregiver.

**Auth required**: Yes (role: caregiver or healthcare)

**Response** `200`:
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Why is my mother repeating stories?",
      "created_at": "..."
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Repeating stories is a common sign...",
      "created_at": "..."
    }
  ]
}
```

---

## Healthcare Worker Endpoints

### `GET /healthcare/dashboard`
Get healthcare worker dashboard summary.

**Auth required**: Yes (role: healthcare)

**Response** `200`:
```json
{
  "total_patients": 5,
  "high_risk_count": 1,
  "medium_risk_count": 2,
  "low_risk_count": 2,
  "recent_sessions": [...]
}
```

---

### `GET /healthcare/patients`
Get list of patients linked to the healthcare worker.

**Auth required**: Yes (role: healthcare)

**Query params**: `risk_level=high&page=1&per_page=20`

**Response** `200`:
```json
{
  "total": 5,
  "patients": [
    {
      "id": "uuid",
      "full_name": "Nenek Ladya",
      "latest_risk_level": "medium",
      "latest_risk_score": 42,
      "last_checkin": "2024-01-02T08:00:00Z",
      "trend": "stable"
    }
  ]
}
```

---

### `GET /healthcare/patients/{patient_id}`
Get detailed view of a specific patient.

**Auth required**: Yes (role: healthcare + linked to patient)

**Response** `200`:
```json
{
  "patient": {...},
  "trend_data": [...],
  "recent_sessions": [...],
  "alerts": [...],
  "reports": [...]
}
```

---

## Reports Endpoints

### `POST /reports/generate`
Generate a monthly report for a patient.

**Auth required**: Yes (role: caregiver or healthcare)

**Request body**:
```json
{
  "patient_user_id": "uuid",
  "report_month": "2024-01-01"
}
```

**Response** `202`:
```json
{
  "report_id": "uuid",
  "status": "generating",
  "message": "Report generation started."
}
```

---

### `GET /reports/{report_id}`
Get a generated report by ID.

**Auth required**: Yes (caregiver or healthcare linked to patient)

**Response** `200`:
```json
{
  "id": "uuid",
  "title": "January 2024 Cognitive Care Summary",
  "report_month": "2024-01-01",
  "patient": {...},
  "checkin_count": 20,
  "avg_risk_score": 41.2,
  "content": {
    "summary": "...",
    "trend": [...],
    "key_indicators": [...],
    "recommendations": [...],
    "disclaimer": "..."
  },
  "pdf_url": "/reports/uuid/download",
  "created_at": "..."
}
```

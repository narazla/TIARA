# 04 — Database Design

## Overview

TIARA uses PostgreSQL as its primary database. All tables use UUID primary keys for security and portability. Timestamps use UTC timezone. Soft deletes are applied to sensitive user and session records.

---

## Entity Relationship Summary

```
users ──< patients ──< caregiver_patient_links >── users (caregivers)
                  ├──< healthcare_patient_links >── users (hcw)
                  └──< checkin_sessions
                              ├──< checkin_answers
                              ├──< media_files
                              ├── transcripts
                              ├── voice_analysis_results
                              ├── facial_analysis_results
                              ├── language_analysis_results
                              └── risk_scores ──< alerts
                                             ──< care_recommendations

users (caregivers) ──< caregiver_pins
users (caregivers) ──< guidance_messages
checkin_sessions ──< reports
```

---

## Tables

### `users`
Stores all platform users regardless of role.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | User identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `full_name` | VARCHAR(255) | NOT NULL | Display name |
| `role` | ENUM | NOT NULL | `elderly`, `caregiver`, `healthcare`, `admin` |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account status |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | Soft delete flag |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last update time |

**Relationships**: One user → one patient profile (if role=elderly), one caregiver record, or one healthcare record.

---

### `patients`
Extended profile for elderly users (role=elderly).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Patient identifier |
| `user_id` | UUID | FK → users.id, UNIQUE | Linked user account |
| `date_of_birth` | DATE | NULL | For age-based risk adjustment |
| `gender` | VARCHAR(10) | NULL | M/F/Other |
| `medical_notes` | TEXT | NULL | General background notes |
| `baseline_established` | BOOLEAN | DEFAULT FALSE | Has enough sessions for baseline |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `caregiver_patient_links`
Many-to-many relationship between caregivers and patients.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Link identifier |
| `caregiver_user_id` | UUID | FK → users.id | Caregiver |
| `patient_user_id` | UUID | FK → users.id | Patient |
| `relationship` | VARCHAR(100) | NULL | e.g., "daughter", "professional" |
| `is_primary` | BOOLEAN | DEFAULT FALSE | Primary caregiver flag |
| `linked_at` | TIMESTAMPTZ | DEFAULT NOW() | When link was established |

**Constraint**: UNIQUE(caregiver_user_id, patient_user_id)

---

### `healthcare_patient_links`
Many-to-many relationship between healthcare workers and patients.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Link identifier |
| `hcw_user_id` | UUID | FK → users.id | Healthcare worker |
| `patient_user_id` | UUID | FK → users.id | Patient |
| `specialty` | VARCHAR(100) | NULL | e.g., "Geriatrics" |
| `linked_at` | TIMESTAMPTZ | DEFAULT NOW() | When linked |

**Constraint**: UNIQUE(hcw_user_id, patient_user_id)

---

### `caregiver_pins`
Stores hashed PIN for caregiver dashboard access.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `caregiver_user_id` | UUID | FK → users.id, UNIQUE | One PIN per caregiver |
| `hashed_pin` | VARCHAR(255) | NOT NULL | Bcrypt hashed 6-digit PIN |
| `failed_attempts` | INTEGER | DEFAULT 0 | Lockout counter |
| `locked_until` | TIMESTAMPTZ | NULL | Lockout expiry time |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `checkin_sessions`
A complete daily check-in session record.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Session identifier |
| `patient_user_id` | UUID | FK → users.id | Patient who did the check-in |
| `status` | ENUM | NOT NULL | `in_progress`, `completed`, `abandoned` |
| `started_at` | TIMESTAMPTZ | NOT NULL | Session start time |
| `completed_at` | TIMESTAMPTZ | NULL | Session end time |
| `question_count` | INTEGER | DEFAULT 0 | Number of questions asked |
| `answer_count` | INTEGER | DEFAULT 0 | Number of answers recorded |
| `processing_status` | ENUM | DEFAULT 'pending' | `pending`, `processing`, `completed`, `failed` |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `checkin_questions`
Predefined question bank for check-ins.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `category` | VARCHAR(100) | NOT NULL | `orientation`, `memory_recall`, `long_term_memory`, `emotional_wellbeing` |
| `question_text` | TEXT | NOT NULL | The question to ask |
| `order_index` | INTEGER | NOT NULL | Display order within category |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether question is in use |

---

### `checkin_answers`
Records each answer given in a session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id | Parent session |
| `question_id` | UUID | FK → checkin_questions.id | Question answered |
| `question_text` | TEXT | NOT NULL | Snapshot of question text at time of answer |
| `category` | VARCHAR(100) | NOT NULL | Category at time of answer |
| `answer_text` | TEXT | NULL | Transcribed or typed answer |
| `recording_started_at` | TIMESTAMPTZ | NULL | When recording began |
| `recording_ended_at` | TIMESTAMPTZ | NULL | When recording ended |
| `response_delay_seconds` | FLOAT | NULL | Time from question display to first speech |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `media_files`
Stores metadata for uploaded audio/video files.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id | Parent session |
| `answer_id` | UUID | FK → checkin_answers.id, NULL | If per-question file |
| `file_type` | ENUM | NOT NULL | `audio`, `video`, `combined` |
| `file_path` | VARCHAR(500) | NOT NULL | Storage path (relative to MEDIA_STORAGE_PATH) |
| `file_size_bytes` | BIGINT | NULL | File size |
| `duration_seconds` | FLOAT | NULL | Media duration |
| `mime_type` | VARCHAR(100) | NULL | e.g., `audio/webm`, `video/webm` |
| `uploaded_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `transcripts`
Stores speech-to-text output.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id | |
| `answer_id` | UUID | FK → checkin_answers.id, NULL | Per-question or full session |
| `media_file_id` | UUID | FK → media_files.id, NULL | Source media |
| `transcript_text` | TEXT | NULL | Full transcribed text |
| `word_count` | INTEGER | NULL | Number of words |
| `provider` | VARCHAR(100) | NULL | e.g., `whisper`, `faster-whisper`, `fallback` |
| `confidence` | FLOAT | NULL | Provider confidence score (0-1) |
| `language` | VARCHAR(10) | DEFAULT 'id' | Language code |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `voice_analysis_results`
Audio feature extraction results.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id, UNIQUE | |
| `duration_seconds` | FLOAT | NULL | Total speaking duration |
| `speech_rate_wpm` | FLOAT | NULL | Words per minute |
| `hesitation_count` | INTEGER | DEFAULT 0 | Filler words detected |
| `repetition_count` | INTEGER | DEFAULT 0 | Repeated phrases detected |
| `pause_count` | INTEGER | DEFAULT 0 | Estimated significant pauses |
| `avg_pause_duration` | FLOAT | NULL | Average pause duration in seconds |
| `voice_risk_score` | FLOAT | NULL | Composite voice risk 0-100 |
| `raw_features` | JSONB | NULL | Additional extracted features |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `facial_analysis_results`
Video/facial processing results.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id, UNIQUE | |
| `video_duration_seconds` | FLOAT | NULL | |
| `face_detected` | BOOLEAN | NULL | Whether face was found in video |
| `face_detection_confidence` | FLOAT | NULL | |
| `avg_response_delay_seconds` | FLOAT | NULL | Estimated time-to-first-response |
| `engagement_score` | FLOAT | NULL | Placeholder for future model |
| `facial_risk_score` | FLOAT | NULL | Composite facial risk 0-100 |
| `provider` | VARCHAR(100) | NULL | e.g., `mediapipe`, `opencv`, `fallback` |
| `raw_features` | JSONB | NULL | Additional extracted features |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `language_analysis_results`
NLP / language processing results.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id, UNIQUE | |
| `orientation_score` | FLOAT | NULL | 0-100 |
| `memory_recall_score` | FLOAT | NULL | 0-100 |
| `coherence_score` | FLOAT | NULL | 0-100 |
| `vocabulary_score` | FLOAT | NULL | 0-100 |
| `emotional_tone` | VARCHAR(50) | NULL | e.g., `positive`, `neutral`, `negative` |
| `language_risk_score` | FLOAT | NULL | Composite language risk 0-100 |
| `raw_analysis` | JSONB | NULL | Full analysis detail |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `risk_scores`
Final composite risk score per session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → checkin_sessions.id, UNIQUE | |
| `patient_user_id` | UUID | FK → users.id | Denormalized for fast queries |
| `risk_score` | FLOAT | NOT NULL | 0-100 composite |
| `risk_level` | ENUM | NOT NULL | `low`, `medium`, `high` |
| `voice_component` | FLOAT | NULL | Voice sub-score |
| `language_component` | FLOAT | NULL | Language sub-score |
| `facial_component` | FLOAT | NULL | Facial sub-score |
| `memory_component` | FLOAT | NULL | Memory recall sub-score |
| `summary` | TEXT | NULL | AI or rule-generated summary |
| `main_indicators` | JSONB | NULL | Array of indicator strings |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `alerts`
Caregiver alerts generated after each session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `patient_user_id` | UUID | FK → users.id | Patient this alert is for |
| `session_id` | UUID | FK → checkin_sessions.id, NULL | Source session |
| `severity` | ENUM | NOT NULL | `info`, `warning`, `critical` |
| `title` | VARCHAR(255) | NOT NULL | Short alert title |
| `description` | TEXT | NOT NULL | Detailed alert message |
| `suggested_action` | TEXT | NULL | Recommended next step |
| `is_read` | BOOLEAN | DEFAULT FALSE | Caregiver read status |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `care_recommendations`
Recommendations generated per session or on schedule.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `patient_user_id` | UUID | FK → users.id | |
| `session_id` | UUID | FK → checkin_sessions.id, NULL | Source session |
| `category` | VARCHAR(100) | NOT NULL | e.g., `cognitive`, `social`, `medical`, `routine` |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | NOT NULL | Full recommendation |
| `priority` | INTEGER | DEFAULT 0 | Higher = more urgent |
| `is_dismissed` | BOOLEAN | DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `guidance_messages`
Dementia Guidance AI conversation history.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `caregiver_user_id` | UUID | FK → users.id | Caregiver who asked |
| `role` | ENUM | NOT NULL | `user`, `assistant` |
| `content` | TEXT | NOT NULL | Message content |
| `provider` | VARCHAR(100) | NULL | LLM provider used |
| `session_context_id` | UUID | NULL | Related session if applicable |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

### `reports`
Generated monthly reports.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | |
| `patient_user_id` | UUID | FK → users.id | |
| `generated_by_user_id` | UUID | FK → users.id, NULL | Who triggered generation |
| `report_month` | DATE | NOT NULL | First day of the report month |
| `title` | VARCHAR(255) | NOT NULL | |
| `content_json` | JSONB | NOT NULL | Full structured report data |
| `pdf_path` | VARCHAR(500) | NULL | If PDF was generated |
| `checkin_count` | INTEGER | NULL | Sessions in this period |
| `avg_risk_score` | FLOAT | NULL | Average risk for month |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

## Migration Strategy

- All schema changes managed via Alembic
- Initial migration: `alembic/versions/001_initial_schema.py`
- Seed data applied via `backend/scripts/seed.py`
- Never manually alter schema in production without a migration file

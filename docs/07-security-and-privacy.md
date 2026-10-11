# 07 — Security and Privacy

## Overview

TIARA handles sensitive health-related behavioral data for elderly users. Security and privacy are foundational requirements, not afterthoughts. Every design decision must account for the vulnerability of the users and the sensitivity of the data.

---

## Authentication

### Password Hashing

- All user passwords are hashed using **bcrypt** via Passlib before storage.
- Plain passwords are never stored, logged, or transmitted after the initial request.
- Bcrypt work factor: minimum 12 rounds.

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### JWT Token Handling

- Access tokens are signed using HS256 with `JWT_SECRET_KEY` (minimum 32 random bytes).
- Token payload includes: `user_id`, `role`, `exp` (expiry).
- Token expiry: configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes).
- Tokens are transmitted in the `Authorization: Bearer <token>` header.
- Tokens are stored in frontend memory or `httpOnly` cookies — never in `localStorage` for production.
- Refresh tokens: post-MVP (add `refresh_token` field and `/auth/refresh` endpoint).

```python
def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```

---

## Role-Based Access Control (RBAC)

### Middleware-Level Enforcement

Route protection is enforced using FastAPI dependencies, not just frontend redirects.

```python
async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_role(*roles: str):
    async def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return _check
```

### Role Permission Matrix

| Endpoint | Elderly | Caregiver | Healthcare | Admin |
|---|---|---|---|---|
| `/auth/*` | ✅ | ✅ | ✅ | ✅ |
| `/elderly/*` | ✅ | ❌ | ❌ | ✅ |
| `/checkins/*` | ✅ | read-only | read-only | ✅ |
| `/caregiver/*` | ❌ | ✅ + PIN | ❌ | ✅ |
| `/guidance/*` | ❌ | ✅ | ✅ | ✅ |
| `/healthcare/*` | ❌ | ❌ | ✅ | ✅ |
| `/reports/*` | ❌ | ✅ | ✅ | ✅ |

---

## Caregiver PIN Protection

The caregiver dashboard is protected by a secondary PIN layer, beyond the JWT auth.

### Why PIN?

Elderly users and caregivers may share a device. The JWT token grants access to the elderly home page. The caregiver dashboard requires an additional 6-digit PIN to prevent the elderly user from seeing clinical analytics.

### PIN Storage

- PIN is **hashed with bcrypt** before storage in `caregiver_pins` table.
- Plain PIN is never stored.
- Failed attempt counter is tracked; 5 failed attempts triggers a 15-minute lockout.

### PIN Verification Flow

```
POST /caregiver/verify-pin
  → Verify JWT token (must be caregiver role)
  → Load hashed PIN from caregiver_pins
  → bcrypt.verify(submitted_pin, hashed_pin)
  → If correct: return short-lived dashboard_token (30 min TTL)
  → If wrong: increment failed_attempts, return 401
  → If locked: return 429 with locked_until timestamp
```

### Dashboard Token

The `dashboard_token` is a separate short-lived JWT with `scope: caregiver_dashboard`. All caregiver dashboard endpoints check for this scope.

---

## Consent-Based Recording

Before any camera or microphone access:

1. Users are presented with a clear consent statement on the Check-In page.
2. Consent is logged to the session record (`consent_given = True`, `consent_at = timestamp`).
3. Browser native permissions dialog is shown (no workarounds).
4. If the user denies permissions, recording does not start and a friendly error is shown.

**Consent statement shown to users**:

> *"TIARA will record your voice and video during this check-in to understand how you're doing. Recordings are stored securely and are only accessible to your caregiver. You can stop at any time."*

---

## Media File Privacy

- Media files are stored on the server filesystem under `MEDIA_STORAGE_PATH`.
- Storage path is **not under the web server's public directory**.
- Files are served only through authenticated API endpoints that verify user ownership.
- File paths in the database are relative paths, not absolute server paths.
- Future production: media files should be encrypted at rest using server-side encryption (AES-256).

---

## Sensitive Health Data Handling

- Cognitive analysis results are never exposed directly to elderly users.
- Risk scores, alerts, and clinical analysis are only accessible to caregivers and healthcare workers.
- The elderly-facing check-in result page shows only warm, non-clinical feedback.
- All API responses for elderly users are filtered to remove clinical data fields.
- All analysis result tables have `patient_user_id` for access control enforcement.

---

## Data Retention and Deletion

- **MVP**: No automated deletion. Manual deletion via admin interface (post-MVP).
- **Future plan**: User data deletion request workflow (GDPR-style).
- Soft delete pattern: `is_deleted = True` on user records; hard delete on orphaned media files.
- Media files should be removed from storage when sessions are deleted.

---

## CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],  # Not "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Secrets Management

- All secrets stored in `.env` file (never committed to version control).
- `.env.example` provided with all keys but no values.
- `.gitignore` explicitly excludes `.env` files.
- JWT secret must be a random string of at least 32 characters.
- Database password must be strong and never use default values.

---

## Safe Medical Disclaimer

TIARA must display the following disclaimer in all caregiver-facing dashboards, reports, and guidance outputs:

> *"TIARA's analysis is not a medical diagnosis. Cognitive risk indicators are informational only and are not intended to replace professional clinical assessment. If you have concerns about a loved one's cognitive health, please consult a qualified healthcare professional."*

And for Dementia Guidance AI:

> *"This guidance is not a medical diagnosis. Please consult a healthcare professional for clinical assessment."*

---

## Security Checklist

- [x] Passwords hashed with bcrypt (min 12 rounds)
- [x] JWT tokens signed, short-lived
- [x] Role-based access enforced on backend, not only frontend
- [x] Caregiver PIN hashed with bcrypt
- [x] PIN brute-force lockout (5 attempts → 15-minute lockout)
- [x] Media files not publicly accessible
- [x] CORS restricted to known frontend origin
- [x] Secrets in environment variables, never hardcoded
- [x] Clinical data hidden from elderly-facing API responses
- [x] Consent logged before recording begins
- [x] Soft delete for user records
- [ ] Refresh token rotation (post-MVP)
- [ ] Media encryption at rest (post-MVP)
- [ ] GDPR-style data deletion workflow (post-MVP)
- [ ] Audit log for caregiver dashboard access (post-MVP)
- [ ] Rate limiting on auth endpoints (post-MVP)

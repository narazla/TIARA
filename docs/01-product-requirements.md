# 01 — Product Requirements

## What is TIARA?

**TIARA** (Thinking, Interaction, And Recall Assistant) is an AI-powered early cognitive risk screening and caregiver support platform designed for elderly users, their caregivers, and healthcare workers.

TIARA uses daily AI-guided conversations — combining voice, video, and language signals — to monitor **cognitive trends over time** and surface early indicators that may warrant timely clinical attention.

> ⚕️ **Important Positioning**: TIARA is **not** a medical diagnosis tool. It is a **cognitive trend monitoring and caregiver support platform**. All outputs are informational and must not replace professional clinical assessment.

---

## Target Users

| User Group | Description |
|---|---|
| **Person in Care (Elderly)** | Older adults (60+) who engage in daily check-ins. Often technology-limited; UI must be simple, warm, and accessible. |
| **Caregiver** | Family members or professional caregivers who monitor trends, receive alerts, and access care recommendations. |
| **Healthcare Worker** | Doctors, nurses, or allied health professionals who need longitudinal data for clinical decision support. |
| **Admin** *(future)* | Platform administrators managing users, configurations, and system health. |

---

## User Roles

### 1. Person in Care / Elderly
- Completes daily AI-guided check-ins
- Uses TIARA Companion for cognitive engagement activities
- Sees only warm, reassuring results — never clinical risk scores

### 2. Caregiver
- Accesses a PIN-protected dashboard
- Views cognitive trend data, alerts, and recommendations
- Chats with Dementia Guidance AI for support
- Downloads or prints monthly care reports

### 3. Healthcare Worker
- Accesses a professional dashboard with patient lists
- Reviews longitudinal cognitive session data
- Adds clinical notes
- Accesses generated reports

### 4. Admin *(post-MVP)*
- Manages platform users and settings
- Reviews system health and usage metrics

---

## Main Problem Statement

Cognitive decline in older adults — including early-stage dementia and mild cognitive impairment (MCI) — often goes undetected for years. By the time families or clinicians notice significant changes, the window for early intervention has passed.

**Key challenges:**
- Families lack tools to track subtle daily changes in memory, language, and orientation
- In-clinic cognitive tests are infrequent (annual or bi-annual)
- Caregivers are often exhausted and underinformed
- Healthcare workers have limited longitudinal behavioral data between visits

---

## Product Goals

1. Enable **daily cognitive trend monitoring** through AI-guided check-ins
2. Provide **caregiver-facing insights** — not raw clinical data — in an accessible format
3. Offer a **supportive companion experience** for elderly users to reduce isolation
4. Surface **early cognitive risk indicators** that encourage timely clinical consultation
5. Support **healthcare workers** with longitudinal behavioral data
6. Build **trust through safety-first design**: consent-based, transparent, and non-alarming

---

## Core Features

### For Elderly Users
- Warm, accessible home page
- Daily AI-guided check-in (voice + video + spoken questions)
- TIARA Companion (story time, memory game, mood check, family memories)
- Simple check-in result (no clinical data shown)

### For Caregivers
- PIN-protected caregiver dashboard
- Cognitive risk trend charts
- Automated alerts for significant changes
- AI-generated care recommendations
- Dementia Guidance AI chatbot
- Monthly report generation

### For Healthcare Workers
- Patient list with risk level filters
- Session history and longitudinal trends
- Clinical notes module
- Report access

---

## Safety Positioning

TIARA is explicitly positioned as:

✅ **Cognitive risk indicator** — a signal, not a verdict  
✅ **Cognitive trend monitoring** — tracking change over time  
✅ **Early cognitive decline screening** — for timely clinical action  
✅ **Caregiver support** — practical guidance for families  
✅ **Not a medical diagnosis** — always stated clearly  
✅ **Encourages timely clinical assessment** — not a replacement  

---

## What the System Must NOT Claim

❌ Do not claim to **diagnose dementia**  
❌ Do not claim **guaranteed detection** of any condition  
❌ Do not use the phrase **medical diagnosis**  
❌ Do not claim to **detect dementia with certainty**  
❌ Do not show clinical risk scores directly to elderly users  
❌ Do not use alarming or scary language in elderly-facing UI  

---

## Disclaimers Required

All caregiver and healthcare-facing pages must include:

> *"TIARA's analysis is not a medical diagnosis. Risk indicators are informational only. Please consult a qualified healthcare professional for clinical assessment."*

All Dementia Guidance AI responses must include:

> *"This guidance is not a medical diagnosis. Please consult a healthcare professional for clinical assessment."*

---

## Accessibility Requirements

- Large, readable fonts for elderly-facing pages
- High color contrast
- Simple language (avoid medical jargon for elderly UI)
- Clear call-to-action buttons
- Friendly, warm tone in all elderly-facing copy
- Camera/microphone permission errors explained gently

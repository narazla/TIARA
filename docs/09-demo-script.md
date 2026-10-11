# 09 — Demo Script

## Competition Demo Script

**Estimated duration**: 8-10 minutes  
**Demo credentials**:
- Elderly: `elderly@tiara.app` / `password123`
- Caregiver: `caregiver@tiara.app` / `password123` / PIN: `123456`
- Healthcare: `doctor@tiara.app` / `password123`

---

## Scene 1: Landing Page (60 seconds)

**URL**: `http://localhost:3000`

**Narration**:

> "TIARA is an AI-powered early cognitive decline screening and caregiver support platform. Every day, millions of families struggle to notice the subtle early signs of cognitive change in their loved ones. TIARA brings early detection into everyday life — through a simple daily check-in."

**Show**:
1. Land on the hero section: "Early cognitive insights, from everyday conversations."
2. Scroll to trust points: Consent-based, Designed with caregivers, Not a medical diagnosis
3. Scroll to "Two experiences, one connected care system" — show the three cards
4. Click "Get Started" → Login page

---

## Scene 2: Login (30 seconds)

**URL**: `http://localhost:3000/login`

**Narration**:

> "Let's log in as Nenek Ladya, our elderly user."

**Actions**:
1. Enter `elderly@tiara.app` / `password123`
2. Click Login
3. System redirects to `/elderly/home`

---

## Scene 3: Elderly Home Page (45 seconds)

**URL**: `http://localhost:3000/elderly/home`

**Narration**:

> "This is Nenek Ladya's home page. The design is intentionally warm and simple — no clinical data, no confusing numbers. She sees a friendly greeting and two clear options."

**Show**:
1. Personalized greeting: "Welcome, Nenek Ladya"
2. Subtitle and today's check-in status: "Your daily check-in is waiting for you today."
3. Two large buttons: Daily Check-In and TIARA Companion
4. Quick peek at profile dropdown

---

## Scene 4: Daily Check-In — Starting (60 seconds)

**URL**: `http://localhost:3000/elderly/check-in`

**Narration**:

> "The Daily Check-In is the core of TIARA. It uses the device's camera and microphone to observe how Nenek Ladya is speaking and responding — just like a gentle conversation."

**Actions**:
1. Click "Daily Check-In"
2. Show the check-in page layout: left = video preview, right = check-in panel
3. Click "Start Check-In"
4. Browser shows camera/microphone permission dialog — grant both
5. Show: camera feed appears, status shows "Camera ready" then "Microphone ready"

---

## Scene 5: Daily Check-In — AI Questions (90 seconds)

**Narration**:

> "TIARA speaks each question aloud. Watch the status — it shows 'TIARA is speaking…' then switches to 'Listening to your answer.' The system records the response."

**Actions**:

**Question 1 — Orientation:**
1. Status: "TIARA is speaking…" (browser TTS speaks "What day is today?")
2. Status changes to "Listening to your answer…"
3. Speak an answer or type one
4. Click "Next Question"
5. Status: "Recording response… ✓"

**Question 2 — Memory Recall:**
1. TTS speaks "What did you eat this morning?"
2. User answers
3. Click "Next Question"

**Show progress bar advancing through categories**: Orientation → Memory Recall → Long-Term Memory → Emotional Wellbeing

---

## Scene 6: Finishing Check-In and AI Processing (45 seconds)

**Narration**:

> "After all questions are answered, Nenek Ladya clicks Finish. The system uploads the session and our AI pipeline begins processing: transcription, voice analysis, language analysis, and risk scoring."

**Actions**:
1. Complete remaining questions quickly (can demonstrate with one click per question)
2. Click "Finish Check-In"
3. Show: "Processing your session…" loading state
4. Automatic redirect to result page

---

## Scene 7: Elderly Result Page (30 seconds)

**URL**: `http://localhost:3000/elderly/check-in/result`

**Narration**:

> "The result page is intentionally gentle. Nenek Ladya sees encouragement and gratitude — not a risk score, not clinical data. Her caregiver sees the full picture separately."

**Show**:
1. "Congratulations, Nenek Ladya 🎉"
2. "Overall, you're doing good."
3. "Thank you for completing today's check-in. Your caregiver can review today's care summary later."
4. Click "Back to Home"

---

## Scene 8: Accessing Caregiver Dashboard (45 seconds)

**Narration**:

> "Now — from the same device, the caregiver wants to check on Nenek Ladya. They access the dashboard through the profile menu."

**Actions**:
1. Click profile dropdown (top right)
2. Click "Dashboard"
3. Redirected to `/caregiver/pin`
4. Show PIN page: "Enter Caregiver PIN — This dashboard contains care insights and is protected for caregiver access."
5. Enter `123456`
6. Redirect to `/caregiver/dashboard`

---

## Scene 9: Caregiver Dashboard (90 seconds)

**URL**: `http://localhost:3000/caregiver/dashboard`

**Narration**:

> "The caregiver dashboard shows the full picture — cognitive risk trend, memory consistency, response delay, speech hesitation, and today's alerts. All real data from the session we just completed."

**Show**:
1. Patient profile card: Nenek Ladya
2. Latest check-in card with risk level badge
3. Cognitive Risk Trend chart (Recharts line chart) — point out the current session's data point
4. Memory consistency indicator
5. Response delay indicator
6. Speech hesitation rate
7. Unread alerts badge

---

## Scene 10: Alerts Page (30 seconds)

**URL**: `http://localhost:3000/caregiver/alerts`

**Narration**:

> "TIARA automatically generates alerts when it detects patterns worth noting — always informational, never alarming."

**Show**:
1. Click "Alerts" in sidebar
2. Show alert cards with severity badges (info/warning)
3. Show one alert: title, description, suggested next step
4. Mark one as read

---

## Scene 11: Care Recommendations (30 seconds)

**URL**: `http://localhost:3000/caregiver/recommendations`

**Narration**:

> "Based on today's session, TIARA generates a practical care plan for the day."

**Show**:
1. Click "Care Recommendations" in sidebar
2. Show sections: Today's Care Plan, Cognitive Activities, Social Suggestions
3. Highlight a specific recommendation

---

## Scene 12: Dementia Guidance AI (60 seconds)

**URL**: `http://localhost:3000/caregiver/guidance`

**Narration**:

> "Caregivers often have urgent questions. The Dementia Guidance AI provides evidence-informed responses — always with a clear medical disclaimer."

**Actions**:
1. Click "Dementia Guidance" in sidebar
2. Click suggested question: "Why is my mother repeating stories?"
3. Show AI response (rule-based or LLM)
4. Show disclaimer: "This guidance is not a medical diagnosis..."
5. Type a follow-up: "Is forgetting names normal aging?"
6. Show response

---

## Scene 13: Reports (30 seconds)

**URL**: `http://localhost:3000/caregiver/reports`

**Narration**:

> "Caregivers can generate a monthly care report to share with their healthcare provider."

**Show**:
1. Click "Reports" in sidebar
2. Show report list card
3. Click a report to view
4. Show report content: patient profile, trend chart, key indicators, recommendations, disclaimer
5. Click "Download PDF"

---

## Scene 14: Healthcare Worker Dashboard (45 seconds)

**Narration**:

> "Finally, let's look at the healthcare worker view. Log in as Dr. Sarah."

**Actions**:
1. Log out
2. Log in as `doctor@tiara.app` / `password123`
3. Redirected to `/healthcare/dashboard`
4. Show patient list with risk level badges
5. Click on Nenek Ladya
6. Show longitudinal trend and session history
7. Show clinical notes section

---

## Closing Statement

**Narration**:

> "TIARA bridges the gap between the home and the clinic. It gives families the tools to notice changes early, caregivers the insights to act thoughtfully, and healthcare workers the longitudinal data they need for better clinical decisions — all while keeping the elderly experience warm, simple, and dignified."

> "TIARA is not a medical diagnosis tool. It is a cognitive trend monitoring and caregiver support platform, designed to encourage timely clinical consultation when it matters most."

---

## Backup Demo Notes

- If camera/microphone not available: pre-record a session using seed data, show dashboard with completed data
- If AI pipeline slow: show cached session result, explain async processing
- If LLM not configured: show rule-based guidance AI response, explain pluggable provider design
- Always emphasize: "This is real data from the session we just completed — not hardcoded demo data"

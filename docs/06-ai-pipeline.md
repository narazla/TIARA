# 06 — AI Pipeline

## Overview

TIARA's AI pipeline converts raw audio/video check-in recordings into structured cognitive trend indicators. The pipeline is designed with **provider abstraction** at every step, enabling real AI components when available and graceful, non-fake fallbacks when not.

> **Critical Design Rule**: No AI logic lives in frontend components. All AI processing runs in backend services. No step returns hardcoded static analysis results.

---

## Pipeline Flow

```
[Check-In Session Completed]
          │
          ▼
[Media Files Uploaded to Storage]
          │
          ▼
[TranscriptionService]
  └── Audio → Text Transcript
          │
          ▼
[VoiceAnalysisService]
  └── Audio + Transcript → Voice Features
          │
          ▼
[LanguageAnalysisService]
  └── Transcript + Answers → Language Features
          │
          ▼
[FacialAnalysisService]
  └── Video File → Facial/Video Features
          │
          ▼
[RiskScoringService]
  └── All Features → Risk Score + Level + Summary
          │
          ▼
[AlertService]
  └── Risk Score + History → Caregiver Alerts
          │
          ▼
[RecommendationService]
  └── Risk Score + Indicators → Care Recommendations
          │
          ▼
[Results stored in database]
[Caregiver dashboard reflects new data]
```

---

## Service 1: TranscriptionService

**Purpose**: Convert recorded audio files to text transcripts.

**Location**: `backend/app/services/transcription_service.py`

### Provider Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class TranscriptionResult:
    text: str
    word_count: int
    language: str
    confidence: float
    provider: str
    segments: list[dict]  # Optional word-level timing

class BaseTranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        ...
```

### WhisperProvider (Primary)

```python
class WhisperProvider(BaseTranscriptionProvider):
    """Uses faster-whisper for local speech-to-text."""
    
    def __init__(self, model_size: str = "base"):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        full_text = " ".join([s.text for s in segments])
        return TranscriptionResult(
            text=full_text.strip(),
            word_count=len(full_text.split()),
            language=info.language,
            confidence=info.language_probability,
            provider="faster-whisper",
            segments=[{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        )
```

### FallbackProvider (When Whisper unavailable)

```python
class FallbackTranscriptionProvider(BaseTranscriptionProvider):
    """
    Fallback when Whisper is not installed.
    Returns an honest empty result — NOT fake text.
    System continues with reduced analysis quality.
    """
    
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="",
            word_count=0,
            language="unknown",
            confidence=0.0,
            provider="fallback-no-stt",
            segments=[]
        )
    
    def is_available(self) -> bool:
        return False
```

### TranscriptionService

```python
class TranscriptionService:
    def __init__(self):
        self.provider = self._load_provider()
    
    def _load_provider(self) -> BaseTranscriptionProvider:
        try:
            return WhisperProvider(model_size=settings.WHISPER_MODEL_SIZE)
        except ImportError:
            logger.warning("faster-whisper not available. Using fallback provider.")
            return FallbackTranscriptionProvider()
    
    async def transcribe_session(self, session_id: str, audio_paths: list[str]) -> list[TranscriptionResult]:
        results = []
        for path in audio_paths:
            result = self.provider.transcribe(path)
            results.append(result)
        return results
```

---

## Service 2: VoiceAnalysisService

**Purpose**: Extract acoustic and linguistic features from audio.

**Location**: `backend/app/services/voice_analysis_service.py`

### Features Extracted

| Feature | Method | Notes |
|---|---|---|
| `duration_seconds` | librosa/pydub duration | File-level |
| `speech_rate_wpm` | word_count / duration_minutes | Requires transcript |
| `hesitation_count` | Count of "um", "uh", "err", "hmm" in transcript | |
| `repetition_count` | Detect repeated 3+ word phrases | |
| `pause_count` | Silence detection in audio | librosa silences |
| `avg_pause_duration` | Mean silent segment length | |
| `voice_risk_score` | Composite formula | See below |

### Voice Risk Score Formula (MVP Rule-Based)

```python
def calculate_voice_risk(features: VoiceFeatures) -> float:
    score = 50.0  # Baseline
    
    # Speech rate penalty (too slow or too fast indicates issue)
    if features.speech_rate_wpm < 80:
        score += 15  # Very slow speech
    elif features.speech_rate_wpm < 100:
        score += 8   # Slightly slow
    elif features.speech_rate_wpm > 180:
        score += 5   # Unusually rapid
    
    # Hesitation penalty
    score += min(features.hesitation_count * 3, 20)
    
    # Repetition penalty
    score += min(features.repetition_count * 5, 15)
    
    # Pause penalty
    if features.avg_pause_duration > 3.0:
        score += 10
    
    # Duration completeness
    if features.duration_seconds < 10:
        score += 10  # Very short responses are a signal
    
    return min(max(score, 0), 100)
```

### Provider-Abstracted Audio Loading

```python
class AudioLoader:
    def load(self, audio_path: str) -> AudioData:
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            return AudioData(signal=y, sample_rate=sr, duration=len(y)/sr)
        except ImportError:
            # Fallback: get duration from file metadata only
            return self._load_metadata_only(audio_path)
```

---

## Service 3: LanguageAnalysisService

**Purpose**: Analyze the content and coherence of spoken answers.

**Location**: `backend/app/services/language_analysis_service.py`

### Analysis Dimensions

#### Orientation Score (0-100)
Measures ability to answer time/place/person questions correctly.
- Correct day/date: +25
- Correct location: +25
- Correct context (who they're talking to): +25
- Fluent response: +25

#### Memory Recall Score (0-100)
Measures ability to recall recent events.
- Recalls breakfast: +25
- Recalls recent visitor: +25
- Responds with detail: +25
- No contradictions: +25

#### Coherence Score (0-100)
Measures whether responses are logically structured.
- Response is on-topic: +30
- No sudden topic drift: +30
- Sentence structure intact: +40

#### Vocabulary Score (0-100)
Measures linguistic richness.
- Unique word ratio (type-token ratio)
- Average word length
- Absence of word-finding pauses in text

#### Language Risk Score Formula

```python
def calculate_language_risk(scores: LanguageScores) -> float:
    # Weighted composite (inverted — lower score = higher risk)
    weighted_avg = (
        scores.orientation * 0.30 +
        scores.memory_recall * 0.30 +
        scores.coherence * 0.25 +
        scores.vocabulary * 0.15
    )
    # Convert competency score to risk score
    language_risk = 100 - weighted_avg
    return round(min(max(language_risk, 0), 100), 2)
```

### LLM-Ready Interface

The LanguageAnalysisService is structured so an LLM provider can replace the rule-based analysis:

```python
class BaseLanguageAnalyzer(ABC):
    @abstractmethod
    def analyze(self, answers: list[AnswerData]) -> LanguageAnalysisResult:
        ...

class RuleBasedAnalyzer(BaseLanguageAnalyzer):
    """MVP: pattern matching and heuristic scoring."""
    ...

class LLMAnalyzer(BaseLanguageAnalyzer):
    """Post-MVP: GPT/Claude/Gemini-powered analysis."""
    ...
```

---

## Service 4: FacialAnalysisService

**Purpose**: Extract behavioral signals from video recordings.

**Location**: `backend/app/services/facial_analysis_service.py`

### MVP Implementation

```python
class FacialAnalysisService:
    def __init__(self):
        self.provider = self._load_provider()
    
    def _load_provider(self) -> BaseFacialProvider:
        try:
            import cv2
            return OpenCVFacialProvider()
        except ImportError:
            try:
                import mediapipe
                return MediaPipeFacialProvider()
            except ImportError:
                logger.warning("No facial analysis library available. Using metadata fallback.")
                return MetadataOnlyFacialProvider()
```

### OpenCVFacialProvider

```python
class OpenCVFacialProvider(BaseFacialProvider):
    def analyze(self, video_path: str) -> FacialAnalysisResult:
        import cv2
        cap = cv2.VideoCapture(video_path)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        face_detected_frames = 0
        sampled_frames = 0
        
        # Sample every 30th frame for performance
        for i in range(0, total_frames, 30):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    face_detected_frames += 1
                sampled_frames += 1
        
        cap.release()
        
        face_ratio = face_detected_frames / sampled_frames if sampled_frames > 0 else 0
        
        return FacialAnalysisResult(
            video_duration_seconds=duration,
            face_detected=face_ratio > 0.5,
            face_detection_confidence=face_ratio,
            facial_risk_score=self._calculate_risk(face_ratio),
            provider="opencv"
        )
```

### MetadataOnlyFacialProvider (Fallback)

```python
class MetadataOnlyFacialProvider(BaseFacialProvider):
    """
    When no video analysis library is available.
    Returns metadata-only result — not fake analysis scores.
    """
    def analyze(self, video_path: str) -> FacialAnalysisResult:
        # Get file size and duration estimate from file metadata
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        return FacialAnalysisResult(
            video_duration_seconds=None,
            face_detected=None,
            face_detection_confidence=None,
            facial_risk_score=None,  # Explicitly None, not 0
            provider="metadata-only",
            notes="Facial analysis library not available. Install opencv-python for full analysis."
        )
```

---

## Service 5: RiskScoringService

**Purpose**: Combine all analysis dimensions into a single risk score.

**Location**: `backend/app/services/risk_scoring_service.py`

### Input

```python
@dataclass
class RiskScoringInput:
    voice_risk_score: float | None
    language_risk_score: float | None
    facial_risk_score: float | None
    memory_recall_score: float | None
    avg_response_delay: float | None
    session_history: list[RiskScore]  # Previous sessions
```

### Composite Risk Formula

```python
def calculate_composite_risk(input: RiskScoringInput) -> float:
    components = []
    weights = []
    
    if input.voice_risk_score is not None:
        components.append(input.voice_risk_score)
        weights.append(0.25)
    
    if input.language_risk_score is not None:
        components.append(input.language_risk_score)
        weights.append(0.35)
    
    if input.facial_risk_score is not None:
        components.append(input.facial_risk_score)
        weights.append(0.20)
    
    if input.memory_recall_score is not None:
        memory_risk = 100 - input.memory_recall_score
        components.append(memory_risk)
        weights.append(0.20)
    
    if not components:
        return 50.0  # Indeterminate — not a fabricated result
    
    # Normalize weights to sum to 1
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]
    
    composite = sum(c * w for c, w in zip(components, normalized))
    return round(min(max(composite, 0), 100), 2)
```

### Risk Level Classification

```
0 – 35:   LOW    (sage green)
36 – 65:  MEDIUM (warm gold)
66 – 100: HIGH   (muted red)
```

### Output Format

```json
{
  "risk_score": 42,
  "risk_level": "medium",
  "voice_component": 38,
  "language_component": 45,
  "facial_component": null,
  "memory_component": 44,
  "summary": "This session shows mild changes in memory recall and response timing compared to the baseline.",
  "main_indicators": [
    "Memory recall score slightly below baseline",
    "Response delay slightly increased",
    "Speech hesitation within normal range"
  ]
}
```

---

## Service 6: RecommendationService

**Purpose**: Generate actionable care recommendations based on session results.

**Location**: `backend/app/services/recommendation_service.py`

### Recommendation Rules

| Condition | Recommendation |
|---|---|
| risk_level = low | Maintain routine, light social activity |
| risk_level = medium | Add cognitive activities, monitor trend |
| risk_level = high | Consider clinical assessment soon |
| memory_recall < 50 | Simple daily recall exercises |
| hesitation_count high | Relaxed conversation, no pressure |
| consecutive medium sessions | Caregiver consultation recommended |

---

## Service 7: AlertService

**Purpose**: Generate caregiver alerts based on session results and historical trends.

**Location**: `backend/app/services/alert_service.py`

### Alert Triggers

| Trigger | Severity | Title |
|---|---|---|
| Check-in missed (no session today) | info | "Daily check-in not completed" |
| risk_level = high | warning | "Elevated cognitive risk indicators" |
| risk_score increased > 15 points vs last session | warning | "Significant change detected in today's session" |
| 3+ consecutive medium/high sessions | warning | "Persistent trend requires attention" |
| memory_recall_score < 40 | warning | "Memory recall score low today" |
| facial analysis failed entirely | info | "Video check-in data incomplete" |

---

## Pipeline Execution Strategy

For the MVP, the pipeline runs **synchronously** after `POST /checkins/{session_id}/finish` in a background task to avoid blocking the HTTP response:

```python
@router.post("/{session_id}/finish")
async def finish_checkin(session_id: str, background_tasks: BackgroundTasks, ...):
    session = await checkin_service.complete_session(session_id)
    background_tasks.add_task(
        ai_pipeline_service.process_session,
        session_id=session_id
    )
    return {"status": "completed", "processing_status": "pending"}
```

Post-MVP: Replace with a proper async task queue (Celery + Redis, or ARQ).

---

## Integration Points for Custom Models

Each service uses a strategy pattern. To inject a custom trained model:

1. Implement the `BaseXxxProvider` abstract class
2. Set the provider class name in environment config
3. The service `_load_provider()` method instantiates the correct provider

No code changes needed in routes, repositories, or other services.

# 06 - AI Pipeline

## Overview

TIARA's AI analysis pipeline processes audio recordings from check-in sessions into structured speech pattern indicators. This document describes what is actually implemented and running in production code.

> **Critical note**: This document describes the real pipeline. Language analysis (orientation, memory, coherence), facial analysis (OpenCV, MediaPipe), and librosa audio processing are NOT part of the real pipeline. Those components exist only in the simulation seed data. The real pipeline uses only faster-whisper for transcription and rule-based voice feature extraction.

---

## Real Pipeline Flow

```
[Check-in session: POST /elderly/checkin/{id}/finish]
    |
    v
[Decrypt .webm.enc files in memory - Fernet]
    |
    v
[faster-whisper transcription per answer]
    - model: base
    - language: id (Indonesian)
    - device: cpu, compute_type: int8
    - word_timestamps: True
    - vad_filter: True
    - beam_size: 1
    |
    v
[Voice feature extraction per answer - fitur_jawaban()]
    - words per minute (from word timestamps, speaking time >= 3s)
    - inter-word pauses >= 0.5 s (AMBANG_JEDA_DETIK)
    - hesitation words: eh, ehm, em, emm, hmm, hm, mm, mmm, ee, eee, anu, uh, um
    - "apa ya" (bigram counted as hesitation)
    - consecutive identical word repetitions
    - response delay (timestamp of first word)
    |
    v
[Feature aggregation - gabung_fitur()]
    - total word count, aggregated pauses, hesitation rate/min
    - mean response delay across answers
    |
    v
[Baseline selection - tentukan_dasar()]
    - if >= 3 prior real sessions: median of last 14 sessions (personal baseline)
    - else: general reference values (ACUAN_UMUM)
      (100 wpm, 0.8s pause, 2.0 hesitations/min, 2.0s response delay)
    |
    v
[Risk scoring - hitung_skor()]
    - deviation per component, clamp(0, 1)
    - weighted sum: wpm=0.3, pause=0.3, response_delay=0.3, hesitation=0.1
    - score = clamp(1.5 + 7.5 * weighted_deviation, 0, 10)
    - Rendah < 4, Sedang 4-6.9, Tinggi >= 7
    |
    v
[Session failure check]
    - if total word count < 5 (MIN_KATA_SESI): mark session failed, create INFO alert
    |
    v
[Save results to database]
    - Transcript (text, word_count, confidence, language="id", provider="faster-whisper-base")
    - VoiceAnalysisResult (speech_rate_wpm, hesitation_count, pause_count, avg_pause_duration,
      voice_risk_score, raw_features JSON with sumber/model/pembanding/komponen)
    - RiskScore (risk_score, risk_level, voice_component=score, language_component=null,
      facial_component=null, memory_component=null, summary, main_indicators)
    |
    v
[Alert generation]
    - score level "high": WARNING alert "Pola bicara hari ini menyimpang dari biasanya"
    - session failed: INFO alert "Check-in hari ini tidak terekam"
    - deduplication: same title not created twice within 12 hours
    |
    v
[Return {status, session_id, perlu_perhatian}]
```

---

## Null Components in Real Sessions

For every real check-in session, the following `risk_scores` fields are always `null`:

- `language_component` - no language analysis runs in real sessions
- `facial_component` - no facial/video analysis; video is not recorded or sent to backend
- `memory_component` - no memory analysis

These fields are populated only in simulated demo data (provider `"simulasi-demo"`) created by the seed script.

---

## Hesitation Detection

Words matched against the hesitation set (KATA_RAGU):

```python
{"eh", "ehm", "em", "emm", "hmm", "hm", "mm", "mmm", "ee", "eee", "anu", "uh", "um"}
```

The bigram `"apa ya"` is also counted as one hesitation instance.

**Known limitation**: faster-whisper frequently removes or normalizes hesitation words during transcription, especially for Indonesian. Hesitation counts tend to be significantly underestimated compared to manual counting. This is a limitation of the transcription model, not a bug in the feature extraction code.

---

## Score Formula

```
deviation_wpm    = max(0, (baseline_wpm - session_wpm) / baseline_wpm)
component_wpm    = min(1, deviation_wpm / 0.4)

deviation_pause  = max(0, session_avg_pause - baseline_avg_pause)
component_pause  = min(1, deviation_pause / max(baseline_avg_pause, 0.3))

deviation_ragu   = max(0, session_ragu_per_min - baseline_ragu_per_min)
component_ragu   = min(1, deviation_ragu / 3.0)

deviation_resp   = max(0, session_response_delay - baseline_response_delay)
component_resp   = min(1, deviation_resp / 3.0)

weights = {wpm: 0.3, pause: 0.3, response_delay: 0.3, hesitation: 0.1}
total_weight = sum of weights for components where data is available
penyimpangan = weighted_sum / total_weight

score = clamp(1.5 + 7.5 * penyimpangan, 0, 10)
```

---

## RAG Guidance Pipeline

Separate from the check-in pipeline. Used for Dementia Guidance AI chat.

```
Caregiver question
    |
    v
[Query expansion - _perluas_pertanyaan()]
    - adds BPSD/DICE keywords for behavioral questions
    - adds sleep-related terms for sleep questions
    - adds hallucination/redirection terms for hallucination questions
    |
    v
[Encode with multilingual-e5-large]
    - prefix: "query: "
    - normalize_embeddings=True
    |
    v
[FAISS index search]
    - index: index_256token.faiss (558 chunks)
    - TOP_K = 6
    - 396 chunks from PNPK Demensia (pages stored 0-indexed; label = index + 1)
    - 162 chunks from Panduan Caregiver Kemenkes (pages stored 1-indexed; used as-is)
    |
    v
[Build prompt - _build_prompt()]
    - context: retrieved chunks with document and page labels
    - instructions: answer only from context, no diagnosis, no medication doses,
      cite sources at end, acknowledge if question is out of scope
    |
    v
[Gemini API - gemini-3.5-flash-lite]
    - up to 3 retries on failure
    - 2s delay between retries
    |
    v
[Return {answer, sources}]
```

**Model warm-up**: the embedding model and FAISS index are loaded once at application startup in a background thread (`_warmup_rag` in `main.py`). The first `/finish` call after a cold start may be slower if the model is still loading.

---

## Simulated Data (Seed Script Only)

The seed script (`backend/app/scripts/seed.py`) generates simulated data for dashboard demonstration. This data populates all four analysis tables:

- `voice_analysis_results` - speech_rate_wpm, hesitation_count, etc.
- `language_analysis_results` - orientation_score, memory_recall_score, coherence_score, vocabulary_score
- `facial_analysis_results` - avg_response_delay, facial_risk_score (provider = "simulasi-demo")
- `risk_scores` - all four components populated

This data is NOT produced by any real AI analysis. It is generated by mathematical formulas with random variation to create plausible-looking trends.

---

## What Is Not in the Pipeline

The following were described in earlier documentation but do NOT exist in the current codebase:

- librosa for audio feature extraction
- OpenCV or MediaPipe for facial/video analysis
- Language analysis (orientation score, memory recall score, coherence score) from real transcripts
- Provider abstraction pattern with BaseTranscriptionProvider/WhisperProvider/FallbackProvider classes
- AIPipelineService orchestration class
- AlertService and RecommendationService as separate service files (alerts and recommendations are generated inline in `checkin_routes.py` and seeded in `seed.py`)

If the codebase evolves to include these, this document should be updated accordingly.

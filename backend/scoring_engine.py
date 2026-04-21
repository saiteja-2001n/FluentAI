"""
scoring_engine.py
─────────────────
Derives 6 evaluation scores from diarization + transcription output.

All scores are in the range 0–100.

Dimensions
──────────
  fluency       — speech rate, pause frequency, turn length
  clarity       — avg word length, vocabulary variation, sentence completeness
  confidence    — speaking pace consistency, turn-start hesitations
  grammar       — heuristic grammar check (optional: swap for LanguageTool)
  pronunciation — proxy from Whisper's avg log-probability per segment
  communication — weighted composite of all above
"""

import re
import json
import math
from typing import List, Dict, Any


# ── helpers ──────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ── individual scorers ────────────────────────────────────────────────────────

def score_fluency(segments: List[Dict]) -> float:
    """
    Fluency proxy:
      • words per minute  (target ~120–160 wpm = 100 pts)
      • penalise very short turns (<3 words) as hesitations
    """
    if not segments:
        return 0.0

    wpms = []
    short_turns = 0
    for seg in segments:
        text = seg.get("text", "")
        words = text.split()
        word_count = len(words)
        duration = seg.get("end", 0) - seg.get("start", 0)
        if duration <= 0:
            continue
        wpm = (word_count / duration) * 60
        wpms.append(wpm)
        if word_count < 3:
            short_turns += 1

    if not wpms:
        return 0.0

    avg_wpm = _avg(wpms)
    # score peaks at 140 wpm, drops off outside 80–200 range
    wpm_score = 100 - abs(avg_wpm - 140) * 0.5
    # penalise hesitation turns
    hesitation_penalty = (short_turns / len(segments)) * 20

    return _clamp(wpm_score - hesitation_penalty)


def score_clarity(segments: List[Dict]) -> float:
    """
    Clarity proxy:
      • type-token ratio (lexical diversity)
      • avg sentence length (very short or very long → lower clarity)
    """
    all_text = " ".join(seg.get("text", "") for seg in segments).lower()
    words = re.findall(r'\b[a-z]+\b', all_text)

    if len(words) < 5:
        return 50.0

    # lexical diversity: unique / total (penalise repetition)
    ttr = len(set(words)) / len(words)
    ttr_score = _clamp(ttr * 130)   # 0.77 ttr → 100

    # avg sentence length: target ~12–18 words
    sentences = re.split(r'[.!?]+', all_text)
    sent_lengths = [len(s.split()) for s in sentences if s.strip()]
    avg_sent = _avg(sent_lengths) if sent_lengths else 0
    length_score = 100 - abs(avg_sent - 15) * 2

    return _clamp((ttr_score * 0.6) + (length_score * 0.4))


def score_confidence(segments: List[Dict]) -> float:
    """
    Confidence proxy:
      • consistency of speaking pace (low variance → high confidence)
      • penalise first-word fillers ("uh", "um", "er")
    """
    if not segments:
        return 0.0

    fillers = {"uh", "um", "er", "ah", "like", "you know"}
    filler_count = 0
    wpms = []

    for seg in segments:
        words = seg.get("text", "").lower().split()
        if words and words[0] in fillers:
            filler_count += 1
        duration = seg.get("end", 0) - seg.get("start", 0)
        if duration > 0 and words:
            wpms.append((len(words) / duration) * 60)

    # pace variance → low variance = high confidence
    if len(wpms) > 1:
        mean_wpm = _avg(wpms)
        variance = _avg([(w - mean_wpm) ** 2 for w in wpms])
        std_dev = math.sqrt(variance)
        pace_score = _clamp(100 - std_dev * 0.5)
    else:
        pace_score = 70.0

    # filler penalty
    filler_ratio = filler_count / len(segments)
    filler_penalty = filler_ratio * 25

    return _clamp(pace_score - filler_penalty)


def score_grammar(segments: List[Dict]) -> float:
    """
    Lightweight heuristic grammar score.
    For production replace this with LanguageTool's REST API.

    Current checks:
      • double spaces / missing capitalisation after full stop
      • obvious subject–verb disagreement patterns
      • sentences ending without punctuation
    """
    all_text = " ".join(seg.get("text", "") for seg in segments)
    sentences = re.split(r'(?<=[.!?])\s+', all_text.strip())

    if not sentences:
        return 50.0

    errors = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # no ending punctuation
        if s[-1] not in ".!?":
            errors += 0.5
        # uncapitalised start
        if s and s[0].islower():
            errors += 0.5
        # simple agreement: "they was", "he were", "i is"
        for pattern in [r'\bthey\s+was\b', r'\bhe\s+were\b', r'\bi\s+is\b',
                        r'\bwe\s+was\b', r'\bshe\s+are\b']:
            if re.search(pattern, s.lower()):
                errors += 1

    error_rate = errors / len(sentences)
    return _clamp(100 - error_rate * 30)


def score_pronunciation(segments: List[Dict]) -> float:
    """
    Pronunciation proxy from Whisper's avg_logprob per segment.
    avg_logprob is in the range (-inf, 0):
      • close to 0   → high confidence → good pronunciation
      • below -0.5   → whisper was uncertain → likely poor pronunciation
    """
    log_probs = [seg.get("avg_logprob") for seg in segments
                 if seg.get("avg_logprob") is not None]

    if not log_probs:
        return 70.0   # default when Whisper doesn't expose logprob

    avg_lp = _avg(log_probs)
    # map [-1.0, 0.0] → [0, 100]
    score = _clamp((avg_lp + 1.0) * 100)
    return score


# ── master scorer ─────────────────────────────────────────────────────────────

def compute_scores(segments: List[Dict]) -> Dict[str, Any]:
    """
    Args:
        segments: list of dicts, each with keys:
            speaker, start, end, text, avg_logprob (optional)

    Returns:
        dict with fluency, clarity, confidence, grammar,
        pronunciation, communication, overall, and recommendations list
    """
    fluency       = round(score_fluency(segments), 1)
    clarity       = round(score_clarity(segments), 1)
    confidence    = round(score_confidence(segments), 1)
    grammar       = round(score_grammar(segments), 1)
    pronunciation = round(score_pronunciation(segments), 1)

    # communication = weighted composite
    communication = round(
        fluency       * 0.25 +
        clarity       * 0.20 +
        confidence    * 0.20 +
        grammar       * 0.20 +
        pronunciation * 0.15,
        1
    )

    overall = round(_avg([fluency, clarity, confidence, grammar, pronunciation]), 1)

    recommendations = _generate_recommendations(
        fluency, clarity, confidence, grammar, pronunciation
    )

    return {
        "fluency":        fluency,
        "clarity":        clarity,
        "confidence":     confidence,
        "grammar":        grammar,
        "pronunciation":  pronunciation,
        "communication":  communication,
        "overall":        overall,
        "recommendations": recommendations   # list[str]
    }


def _generate_recommendations(
    fluency: float,
    clarity: float,
    confidence: float,
    grammar: float,
    pronunciation: float
) -> List[str]:
    tips = []

    if fluency < 65:
        tips.append("Practice reading aloud daily to improve speaking pace and reduce unnatural pauses.")
    elif fluency < 80:
        tips.append("Work on maintaining a consistent speaking rhythm — try paced reading exercises.")

    if clarity < 65:
        tips.append("Focus on expanding vocabulary and forming complete, well-structured sentences.")
    elif clarity < 80:
        tips.append("Vary your sentence structures more to improve overall clarity and engagement.")

    if confidence < 65:
        tips.append("Reduce filler words (uh, um, like) by practising planned speech with short monologues.")
    elif confidence < 80:
        tips.append("Work on steadying your speaking pace — record yourself and review the playback.")

    if grammar < 65:
        tips.append("Review subject–verb agreement and sentence ending punctuation conventions.")
    elif grammar < 80:
        tips.append("Read more complex texts to naturally absorb grammatical patterns.")

    if pronunciation < 65:
        tips.append("Use a pronunciation app (e.g. ELSA Speak) to target specific sound patterns.")
    elif pronunciation < 80:
        tips.append("Focus on stressed syllables and connected speech for clearer pronunciation.")

    if not tips:
        tips.append("Excellent performance! Challenge yourself with more complex vocabulary and longer turns.")

    return tips
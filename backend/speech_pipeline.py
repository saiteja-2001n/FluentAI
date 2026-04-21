"""
speech_pipeline.py
──────────────────
Whisper transcription + pyannote diarization + score computation.
All heavy models are loaded lazily so startup is fast.
"""

import os
import torch
import warnings
import numpy as np
from typing import Dict, Any

from faster_whisper import WhisperModel
from .scoring_engine import compute_scores
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

load_dotenv()

# ── model registry (lazy-loaded singletons) ──────────────────────────────────

_whisper_model = None
_diarization_pipeline = None


def _get_whisper() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        model_size = os.getenv("WHISPER_MODEL", "base")
        _whisper_model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )
    return _whisper_model


def _get_diarization():
    global _diarization_pipeline
    if _diarization_pipeline is None:
        from pyannote.audio import Pipeline

        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "HF_TOKEN not set. Get one from https://huggingface.co/settings/tokens"
            )

        _diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )

    return _diarization_pipeline


# ── main processing function ──────────────────────────────────────────────────

def process_audio(audio_data: Dict) -> Dict[str, Any]:
    """
    Run full pipeline on audio already loaded into memory.

    Expected audio_data keys:
        waveform    – torch.Tensor or numpy array (1D or 2D)
        sample_rate – int
    """

    waveform = audio_data["waveform"]
    sample_rate = audio_data["sample_rate"]

    # ── 1. Convert to numpy mono (1D) for Whisper ─────────────────────────────
    if hasattr(waveform, "numpy"):
        audio_np = waveform.numpy()
    else:
        audio_np = np.array(waveform, dtype=np.float32)

    if audio_np.ndim > 1:
        audio_np = audio_np.mean(axis=0)

    # ── 2. Transcribe with Whisper ────────────────────────────────────────────
    whisper = _get_whisper()

    segments_generator, _ = whisper.transcribe(
        audio_np,
        language="en",
        word_timestamps=False
    )

    transcription_segments = []
    for seg in segments_generator:
        transcription_segments.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
            "avg_logprob": getattr(seg, "avg_logprob", None)
        })

    # ── 3. Speaker diarization ────────────────────────────────────────────────
    pipeline = _get_diarization()

    # pyannote requires a 2D torch tensor of shape (channels, samples)
    waveform_tensor = torch.tensor(audio_np, dtype=torch.float32).unsqueeze(0)  # (1, N)

    diarization_output = pipeline({
        "waveform": waveform_tensor,
        "sample_rate": sample_rate
    })

    # ✅ FINAL FIX: DiarizeOutput.speaker_diarization is the Annotation object
    annotation = diarization_output.speaker_diarization

    speaker_windows = []
    for segment, _, speaker in annotation.itertracks(yield_label=True):
        speaker_windows.append({
            "speaker": speaker,
            "start": float(segment.start),
            "end": float(segment.end)
        })

    # ── 4. Align transcription segments with speaker windows ──────────────────
    final_segments = []

    for t_seg in transcription_segments:
        matched_speaker = _match_speaker(t_seg, speaker_windows)

        final_segments.append({
            "speaker": matched_speaker,
            "start": t_seg["start"],
            "end": t_seg["end"],
            "text": t_seg["text"],
            "avg_logprob": t_seg["avg_logprob"]
        })

    # ── 5. Compute scores per speaker ─────────────────────────────────────────
    speaker_segments_map: Dict[str, list] = {}

    for seg in final_segments:
        sp = seg["speaker"]
        speaker_segments_map.setdefault(sp, []).append(seg)

    scores_per_speaker = {}

    for speaker, segs in speaker_segments_map.items():
        result = compute_scores(segs)

        scores_per_speaker[speaker] = {
            "scores": {k: v for k, v in result.items() if k != "recommendations"},
            "recommendations": result["recommendations"]
        }

    return {
        "segments": final_segments,
        "scores_per_speaker": scores_per_speaker
    }


# ── helper ────────────────────────────────────────────────────────────────────

def _match_speaker(t_seg: Dict, speaker_windows: list) -> str:
    """
    Match a transcription segment to a speaker using maximum time overlap.
    Returns 'UNKNOWN' if no overlap is found.
    """

    best_speaker = "UNKNOWN"
    best_overlap = 0.0

    for sw in speaker_windows:
        overlap_start = max(t_seg["start"], sw["start"])
        overlap_end = min(t_seg["end"], sw["end"])
        overlap = max(0.0, overlap_end - overlap_start)

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = sw["speaker"]

    return best_speaker
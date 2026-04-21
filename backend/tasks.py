"""
tasks.py
────────
Celery tasks for async audio processing.

Start the worker with:
    celery -A app.tasks worker --loglevel=info
"""

import os
import json
import torch
import librosa
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "audio_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,  # one heavy task at a time per worker
)


@celery_app.task(bind=True, name="process_audio_task")
def process_audio_task(self, audio_file_id: int, session_id: int, file_path: str):
    """
    Heavy background task:
      1. Load audio from disk
      2. Run Whisper + diarization + scoring
      3. Write segments and scores to DB
      4. Update session status
    """

    # Import here to avoid circular imports
    from .database import SessionLocal
    from . import crud
    from .speech_pipeline import process_audio
    from . import models

    db = SessionLocal()

    try:
        # ✅ Step 1 — mark session as processing
        crud.update_session_status(db, session_id, "processing")

        # ✅ Step 2 — load audio
        waveform_np, sample_rate = librosa.load(file_path, sr=None, mono=False)

        if waveform_np.ndim == 1:
            waveform = torch.from_numpy(waveform_np).unsqueeze(0)
        else:
            waveform = torch.from_numpy(waveform_np)

        audio_data = {"waveform": waveform, "sample_rate": sample_rate}

        # ✅ Step 3 — update duration
        duration = waveform.shape[-1] / sample_rate
        audio_file = db.query(models.AudioFile).get(audio_file_id)

        if audio_file:
            audio_file.duration = duration
            db.commit()

        # ✅ Step 4 — run pipeline
        result = process_audio(audio_data)

        # ✅ Step 5 — save segments
        for seg in result["segments"]:
            crud.create_segment(
                db,
                audio_file_id=audio_file_id,
                speaker_label=seg["speaker"],
                start_time=seg["start"],
                end_time=seg["end"],
                transcript=seg["text"]
            )

        # ✅ Step 6 — save scores
        for speaker_label, speaker_data in result["scores_per_speaker"].items():
            crud.create_speaker_score(
                db,
                session_id=session_id,
                speaker_label=speaker_label,
                scores=speaker_data["scores"],
                recommendations=json.dumps(speaker_data["recommendations"])
            )

        # ✅ Step 7 — mark completed
        crud.update_session_status(db, session_id, "completed")

        # ✅ Step 8 — cleanup file
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "completed",
            "session_id": session_id
        }

    except Exception as exc:
        crud.update_session_status(db, session_id, "failed")
        raise self.retry(exc=exc, max_retries=0)

    finally:
        db.close()
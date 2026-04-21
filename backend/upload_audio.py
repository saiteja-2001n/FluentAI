import os
import json
import librosa
import torch
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from .db_dependency import get_db
from . import crud, schemas, models
from .speech_pipeline import process_audio

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # ✅ Step 1 — Save file to disk
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)

        # ✅ Step 2 — Load audio
        waveform, sample_rate = librosa.load(file_path, sr=None, mono=False)

        if waveform.ndim == 1:
            waveform = torch.from_numpy(waveform).unsqueeze(0)
        else:
            waveform = torch.from_numpy(waveform)

        audio_data = {
            "waveform": waveform,
            "sample_rate": sample_rate
        }

        duration = waveform.shape[-1] / sample_rate

        # ✅ Step 3 — Create session
        session_data = schemas.SessionCreate(
            session_name=file.filename,
            session_type="individual"
        )
        db_session = crud.create_session(db, session_data)

        # ✅ Step 4 — Save audio file
        audio_db_data = schemas.AudioCreate(
            session_id=db_session.session_id,
            file_name=file.filename,
            file_path=file_path,
            duration=duration
        )
        db_audio = crud.create_audio(db, audio_db_data)

        # ✅ Step 5 — Run processing (SYNC)
        results = process_audio(audio_data)

        final_segments = results["segments"]
        scores_per_speaker = results["scores_per_speaker"]

        # ✅ Step 6 — Create speakers
        speaker_id_map = {}
        for speaker_label in scores_per_speaker.keys():
            db_speaker = models.Speaker(
                session_id=db_session.session_id,
                speaker_label=speaker_label,
                user_id=None
            )
            db.add(db_speaker)
            db.flush()

            speaker_id_map[speaker_label] = db_speaker.speaker_id

        # ✅ Step 7 — Save segments
        for seg in final_segments:
            speaker_label = seg.get("speaker", "UNKNOWN")
            speaker_id = speaker_id_map.get(speaker_label)

            segment_data = schemas.SegmentCreate(
                audio_id=db_audio.audio_id,
                speaker_id=speaker_id,
                start_time=seg["start"],
                end_time=seg["end"],
                duration=seg["end"] - seg["start"],
                text=seg.get("text", "")
            )
            crud.create_segment(db, segment_data)

        # ✅ Step 8 — Save scores
        for speaker_label, speaker_data in scores_per_speaker.items():
            scores = speaker_data["scores"]
            recommendations = speaker_data["recommendations"]

            score_data = schemas.SpeakerScoreCreate(
                session_id=db_session.session_id,
                speaker_label=speaker_label,
                fluency=scores.get("fluency"),
                clarity=scores.get("clarity"),
                confidence=scores.get("confidence"),
                grammar=scores.get("grammar"),
                pronunciation=scores.get("pronunciation"),
                communication=scores.get("communication"),
                overall=scores.get("overall"),
                recommendations=json.dumps(recommendations)
            )
            crud.create_speaker_score(db, score_data)

        # ============================================================
        # ✅ ORIGINAL CODE (BACKUP)
        # ============================================================
        """
        db.commit()
        crud.update_session_status(db, db_session.session_id, "completed")

        return {
            "session_id": db_session.session_id,
            "audio_id": db_audio.audio_id,
            "duration": duration,
            "segments": final_segments,
            "scores_per_speaker": scores_per_speaker
        }
        """

        # ============================================================
        # 🔥 UPDATED CODE WITH AUTO NOTIFICATION
        # ============================================================

        # Step 9 — Commit & mark completed
        db.commit()
        crud.update_session_status(db, db_session.session_id, "completed")

        # 🔔 AUTO NOTIFICATION (NEW — SAFE)
        try:
            notif = models.Notification(
                user_id=1,  # temporary user
                message=f"Session {db_session.session_id} report is ready",
                status="pending"
            )
            db.add(notif)
            db.commit()
        except Exception as e:
            print("Notification error:", e)

        return {
            "session_id": db_session.session_id,
            "audio_id": db_audio.audio_id,
            "duration": duration,
            "segments": final_segments,
            "scores_per_speaker": scores_per_speaker
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
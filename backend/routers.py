"""
routers.py
──────────
All non-upload API routes.
"""

import json
from io import BytesIO
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .db_dependency import get_db
from . import crud, schemas, models
from .pdf_report import generate_session_report

router = APIRouter()


# ─────────────── Students ───────────────────────────────────────────────────

@router.post("/students", response_model=schemas.StudentResponse, tags=["students"])
def create_student(data: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db, data)


@router.get("/students", response_model=List[schemas.StudentResponse], tags=["students"])
def list_students(db: Session = Depends(get_db)):
    return crud.get_students(db)


@router.get("/students/{student_id}", response_model=schemas.StudentResponse, tags=["students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/students/{student_id}/scores",
            response_model=List[schemas.SpeakerScoreResponse], tags=["students"])
def get_student_scores(student_id: int, db: Session = Depends(get_db)):
    return crud.get_scores_for_student(db, student_id)


@router.get("/students/{student_id}/progress",
            response_model=schemas.StudentProgressResponse, tags=["students"])
def get_student_progress(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    rows = crud.get_student_progress(db, student_id)

    sessions_data = [
        schemas.SessionScoreSummary(
            session_id=r.session_id,
            session_name=r.session_name,
            started_at=r.started_at,
            fluency=r.fluency,
            clarity=r.clarity,
            confidence=r.confidence,
            grammar=r.grammar,
            pronunciation=r.pronunciation,
            communication=r.communication,
            overall=r.overall
        )
        for r in rows
    ]

    return schemas.StudentProgressResponse(
        student_id=student.id,
        student_name=student.name,
        sessions=sessions_data
    )


# ─────────────── Sessions ───────────────────────────────────────────────────

@router.get("/sessions", response_model=List[schemas.SessionResponse], tags=["sessions"])
def list_sessions(db: Session = Depends(get_db)):
    return crud.get_sessions(db)


@router.get("/sessions/{session_id}", response_model=schemas.SessionResponse, tags=["sessions"])
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
"""
routers.py
──────────
All non-upload API routes.
"""

import json
from io import BytesIO
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .db_dependency import get_db
from . import crud, schemas, models
from .pdf_report import generate_session_report

router = APIRouter()


# ─────────────── Students ───────────────────────────────────────────────────

@router.post("/students", response_model=schemas.StudentResponse, tags=["students"])
def create_student(data: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db, data)


@router.get("/students", response_model=List[schemas.StudentResponse], tags=["students"])
def list_students(db: Session = Depends(get_db)):
    return crud.get_students(db)


@router.get("/students/{student_id}", response_model=schemas.StudentResponse, tags=["students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.get("/students/{student_id}/scores",
            response_model=List[schemas.SpeakerScoreResponse], tags=["students"])
def get_student_scores(student_id: int, db: Session = Depends(get_db)):
    return crud.get_scores_for_student(db, student_id)


@router.get("/students/{student_id}/progress",
            response_model=schemas.StudentProgressResponse, tags=["students"])
def get_student_progress(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    rows = crud.get_student_progress(db, student_id)

    sessions_data = [
        schemas.SessionScoreSummary(
            session_id=r.session_id,
            session_name=r.session_name,
            started_at=r.started_at,
            fluency=r.fluency,
            clarity=r.clarity,
            confidence=r.confidence,
            grammar=r.grammar,
            pronunciation=r.pronunciation,
            communication=r.communication,
            overall=r.overall
        )
        for r in rows
    ]

    return schemas.StudentProgressResponse(
        student_id=student.id,
        student_name=student.name,
        sessions=sessions_data
    )


# ─────────────── Sessions ───────────────────────────────────────────────────

@router.get("/sessions", response_model=List[schemas.SessionResponse], tags=["sessions"])
def list_sessions(db: Session = Depends(get_db)):
    return crud.get_sessions(db)


@router.get("/sessions/{session_id}", response_model=schemas.SessionResponse, tags=["sessions"])
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/status", tags=["sessions"])
def get_session_status(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status":     session.status,
    }


@router.get("/sessions/{session_id}/scores",
            response_model=List[schemas.SpeakerScoreResponse], tags=["sessions"])
def get_session_scores(session_id: int, db: Session = Depends(get_db)):
    return crud.get_scores_for_session(db, session_id)


@router.get("/sessions/{session_id}/segments",
            response_model=List[schemas.SegmentResponse], tags=["sessions"])
def get_session_segments(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session or not session.audio_files:
        raise HTTPException(status_code=404, detail="Session or audio not found")
    audio_id = session.audio_files[0].audio_id
    return crud.get_segments_for_audio(db, audio_id)


# ─────────────── Assign student to speaker ──────────────────────────────────

@router.patch("/sessions/{session_id}/speakers/{speaker_label}/assign",
              tags=["sessions"])
def assign_speaker_to_student(
    session_id: int,
    speaker_label: str,
    student_id: int,
    db: Session = Depends(get_db)
):
    score = (db.query(models.SpeakerScore)
               .filter(
                   models.SpeakerScore.session_id == session_id,
                   models.SpeakerScore.speaker_label == speaker_label
               ).first())
    if not score:
        raise HTTPException(status_code=404, detail="Speaker score not found")

    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    score.student_id = student_id
    db.commit()
    db.refresh(score)
    return {"message": f"{speaker_label} assigned to {student.name}"}


# ─────────────── Reports ────────────────────────────────────────────────────

@router.get("/reports/{session_id}/pdf", tags=["reports"])
def download_session_report(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.audio_files:
        raise HTTPException(status_code=404, detail="No audio found for this session")
    audio = session.audio_files[0]
    segments_db = crud.get_segments_for_audio(db, audio.audio_id)
    scores_db   = crud.get_scores_for_session(db, session_id)

    segments = [
        {
            "speaker": seg.speaker.speaker_label if seg.speaker else "Unknown",
            "start":   seg.start_time,
            "end":     seg.end_time,
            "text":    seg.text or "",
        }
        for seg in segments_db
    ]

    scores_per_speaker = {}
    for sc in scores_db:
        recs = []
        if sc.recommendations:
            try:
                recs = json.loads(sc.recommendations)
            except Exception:
                recs = [sc.recommendations]

        scores_per_speaker[sc.speaker_label] = {
            "scores": {
                "fluency": sc.fluency,
                "clarity": sc.clarity,
                "confidence": sc.confidence,
                "grammar": sc.grammar,
                "pronunciation": sc.pronunciation,
                "communication": sc.communication,
                "overall": sc.overall,
            },
            "recommendations": recs,
        }

    session_data = {
        "session_id": session_id,
        "audio_id": audio.audio_id,
        "duration": audio.duration or 0,
        "segments": segments,
        "scores_per_speaker": scores_per_speaker,
    }

    progress_data = None
    if scores_db and scores_db[0].student_id:
        raw_progress = crud.get_student_progress(db, scores_db[0].student_id)
        progress_data = [
            {
                "session_name": row.session_name or f"Session {row.session_id}",
                "fluency": row.fluency,
                "clarity": row.clarity,
                "confidence": row.confidence,
                "grammar": row.grammar,
                "pronunciation": row.pronunciation,
                "communication": row.communication,
                "overall": row.overall,
            }
            for row in raw_progress
        ]

    pdf_bytes = generate_session_report(session_data, progress_data)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session_id}_report.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


# ============================================================
# 🔔 NOTIFICATIONS (ADDED — SAFE, NO CHANGES ABOVE)
# ============================================================

@router.get("/notifications/{user_id}", tags=["notifications"])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Notification)\
        .filter(models.Notification.user_id == user_id)\
        .order_by(models.Notification.created_at.desc())\
        .all()


@router.post("/notifications", tags=["notifications"])
def create_notification(user_id: int, message: str, db: Session = Depends(get_db)):
    notif = models.Notification(
        user_id=user_id,
        message=message,
        status="pending"
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/notifications/{notification_id}/read", tags=["notifications"])
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).get(notification_id)

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.status = "read"
    db.commit()

    return {"message": "Notification marked as read"}

@router.get("/sessions/{session_id}/status", tags=["sessions"])
def get_session_status(session_id: int, db: Session = Depends(get_db)):
    """Poll this endpoint from the frontend to check processing progress."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "status":     session.status,
    }


@router.get("/sessions/{session_id}/scores",
            response_model=List[schemas.SpeakerScoreResponse], tags=["sessions"])
def get_session_scores(session_id: int, db: Session = Depends(get_db)):
    return crud.get_scores_for_session(db, session_id)


@router.get("/sessions/{session_id}/segments",
            response_model=List[schemas.SegmentResponse], tags=["sessions"])
def get_session_segments(session_id: int, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session or not session.audio_files:
        raise HTTPException(status_code=404, detail="Session or audio not found")
    audio_id = session.audio_files[0].audio_id
    return crud.get_segments_for_audio(db, audio_id)


# ─────────────── Assign student to speaker ──────────────────────────────────

@router.patch("/sessions/{session_id}/speakers/{speaker_label}/assign",
              tags=["sessions"])
def assign_speaker_to_student(
    session_id: int,
    speaker_label: str,
    student_id: int,
    db: Session = Depends(get_db)
):
    score = (db.query(models.SpeakerScore)
               .filter(
                   models.SpeakerScore.session_id == session_id,
                   models.SpeakerScore.speaker_label == speaker_label
               ).first())
    if not score:
        raise HTTPException(status_code=404, detail="Speaker score not found")

    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    score.student_id = student_id
    db.commit()
    db.refresh(score)
    return {"message": f"{speaker_label} assigned to {student.name}"}


# ─────────────── Reports ────────────────────────────────────────────────────

@router.get("/reports/{session_id}/pdf", tags=["reports"])
def download_session_report(session_id: int, db: Session = Depends(get_db)):
    """
    Returns a professional downloadable PDF report for the given session.
    Uses pdf_report.py for rich formatting — score bars, transcript, progress trends.
    """
    # 1. Fetch session
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Fetch audio + segments
    if not session.audio_files:
        raise HTTPException(status_code=404, detail="No audio found for this session")
    audio = session.audio_files[0]
    segments_db = crud.get_segments_for_audio(db, audio.audio_id)
    scores_db   = crud.get_scores_for_session(db, session_id)

    # 3. Build segments list
    segments = [
        {
            "speaker": seg.speaker.speaker_label if seg.speaker else "Unknown",
            "start":   seg.start_time,
            "end":     seg.end_time,
            "text":    seg.text or "",
        }
        for seg in segments_db
    ]

    # 4. Build scores_per_speaker dict
    scores_per_speaker = {}
    for sc in scores_db:
        recs = []
        if sc.recommendations:
            try:
                recs = json.loads(sc.recommendations)
            except Exception:
                recs = [sc.recommendations]

        scores_per_speaker[sc.speaker_label] = {
            "scores": {
                "fluency":       sc.fluency,
                "clarity":       sc.clarity,
                "confidence":    sc.confidence,
                "grammar":       sc.grammar,
                "pronunciation": sc.pronunciation,
                "communication": sc.communication,
                "overall":       sc.overall,
            },
            "recommendations": recs,
        }

    # 5. Build session_data dict for pdf_report.py
    session_data = {
        "session_id":         session_id,
        "audio_id":           audio.audio_id,
        "duration":           audio.duration or 0,
        "segments":           segments,
        "scores_per_speaker": scores_per_speaker,
    }

    # 6. Optional progress trend (if speaker is assigned to a student)
    progress_data = None
    if scores_db and scores_db[0].student_id:
        raw_progress = crud.get_student_progress(db, scores_db[0].student_id)
        progress_data = [
            {
                "session_name":  row.session_name or f"Session {row.session_id}",
                "fluency":       row.fluency,
                "clarity":       row.clarity,
                "confidence":    row.confidence,
                "grammar":       row.grammar,
                "pronunciation": row.pronunciation,
                "communication": row.communication,
                "overall":       row.overall,
            }
            for row in raw_progress
        ]

    # 7. Generate PDF bytes using pdf_report.py
    pdf_bytes = generate_session_report(session_data, progress_data)

    # 8. Stream back as downloadable PDF
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session_id}_report.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )
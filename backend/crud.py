from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from . import models, schemas


# ─────────────── Student ───────────────

def create_student(db: DBSession, data: schemas.StudentCreate) -> models.Student:
    student = models.Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_students(db: DBSession) -> List[models.Student]:
    return db.query(models.Student).order_by(models.Student.name).all()


def get_student(db: DBSession, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


# ─────────────── Session ───────────────

def create_session(db: DBSession, data: schemas.SessionCreate) -> models.Session:
    session = models.Session(
        session_name=data.session_name,
        session_type=data.session_type,
        status="recording"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_sessions(db: DBSession) -> List[models.Session]:
    return db.query(models.Session).order_by(models.Session.started_at.desc()).all()


def get_session(db: DBSession, session_id: int) -> Optional[models.Session]:
    return db.query(models.Session).filter(models.Session.session_id == session_id).first()


def update_session_status(db: DBSession, session_id: int, status: str):
    session = get_session(db, session_id)
    if session:
        session.status = status
        db.commit()
        db.refresh(session)
    return session


# ─────────────── Audio File ───────────────

def create_audio(db: DBSession, data: schemas.AudioCreate) -> models.AudioFile:
    audio = models.AudioFile(
        session_id=data.session_id,
        file_name=data.file_name,
        file_path=data.file_path,
        duration=data.duration
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def get_audio_files(db: DBSession, session_id: int) -> List[models.AudioFile]:
    return db.query(models.AudioFile).filter(models.AudioFile.session_id == session_id).all()


# ─────────────── Speaker Segment ───────────────

def create_segment(db: DBSession, data: schemas.SegmentCreate) -> models.SpeakerSegment:
    seg = models.SpeakerSegment(
        audio_id=data.audio_id,
        speaker_id=data.speaker_id,
        start_time=data.start_time,
        end_time=data.end_time,
        duration=data.duration,
        text=data.text  # ✅ IMPORTANT (you missed earlier)
    )
    db.add(seg)
    db.commit()
    db.refresh(seg)
    return seg


def get_segments_for_audio(db: DBSession, audio_id: int) -> List[models.SpeakerSegment]:
    return (
        db.query(models.SpeakerSegment)
        .filter(models.SpeakerSegment.audio_id == audio_id)
        .order_by(models.SpeakerSegment.start_time)
        .all()
    )


# ─────────────── Speaker Score ───────────────

def create_speaker_score(db: DBSession, data: schemas.SpeakerScoreCreate) -> models.SpeakerScore:
    score = models.SpeakerScore(
        session_id=data.session_id,
        student_id=data.student_id,
        speaker_label=data.speaker_label,
        fluency=data.fluency,
        clarity=data.clarity,
        confidence=data.confidence,
        grammar=data.grammar,
        pronunciation=data.pronunciation,
        communication=data.communication,
        overall=data.overall,
        recommendations=data.recommendations
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def get_scores_for_session(db: DBSession, session_id: int) -> List[models.SpeakerScore]:
    return db.query(models.SpeakerScore).filter(models.SpeakerScore.session_id == session_id).all()


def get_scores_for_student(db: DBSession, student_id: int) -> List[models.SpeakerScore]:
    return (
        db.query(models.SpeakerScore)
        .filter(models.SpeakerScore.student_id == student_id)
        .order_by(models.SpeakerScore.scored_at)
        .all()
    )


# ─────────────── Progress Trend ───────────────

def get_student_progress(db: DBSession, student_id: int):
    rows = (
        db.query(
            models.Session.session_id.label("session_id"),
            models.Session.session_name.label("session_name"),
            models.Session.started_at.label("started_at"),
            models.SpeakerScore.fluency,
            models.SpeakerScore.clarity,
            models.SpeakerScore.confidence,
            models.SpeakerScore.grammar,
            models.SpeakerScore.pronunciation,
            models.SpeakerScore.communication,
            models.SpeakerScore.overall,
        )
        .join(
            models.SpeakerScore,
            models.Session.session_id == models.SpeakerScore.session_id
        )
        .filter(models.SpeakerScore.student_id == student_id)
        .order_by(models.Session.started_at)
        .all()
    )
    return rows
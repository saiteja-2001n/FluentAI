from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ─────────────── Student ───────────────

class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    class_name: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    class_name: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────── Session ───────────────

class SessionCreate(BaseModel):
    session_name: Optional[str] = None
    session_type: Optional[str] = "discussion"


class SessionResponse(BaseModel):
    session_id: int
    session_name: Optional[str]
    session_type: str
    status: str
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────── Audio File ───────────────

class AudioCreate(BaseModel):
    session_id: int
    file_name: str
    file_path: str
    duration: Optional[float] = Field(default=None, ge=0)


class AudioFileResponse(BaseModel):
    audio_id: int
    session_id: int
    file_name: str
    duration: Optional[float]
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────── Segment ───────────────

class SegmentCreate(BaseModel):
    audio_id: int
    speaker_id: Optional[int] = None
    start_time: float = Field(..., ge=0)
    end_time: float = Field(..., ge=0)
    duration: Optional[float] = Field(default=None, ge=0)
    text: Optional[str] = None              # ✅ added — transcript text


class SegmentResponse(BaseModel):
    segment_id: int
    audio_id: int
    speaker_id: Optional[int]
    start_time: float
    end_time: float
    duration: Optional[float]
    text: Optional[str] = None              # ✅ added — transcript text

    model_config = ConfigDict(from_attributes=True)


# ─────────────── Speaker Score ───────────────

class SpeakerScoreCreate(BaseModel):
    session_id: int
    speaker_label: str
    student_id: Optional[int] = None
    fluency: Optional[float] = None
    clarity: Optional[float] = None
    confidence: Optional[float] = None
    grammar: Optional[float] = None
    pronunciation: Optional[float] = None
    communication: Optional[float] = None
    overall: Optional[float] = None
    recommendations: Optional[str] = None


class SpeakerScoreResponse(BaseModel):
    id: int
    session_id: int
    student_id: Optional[int]
    speaker_label: str
    fluency: Optional[float]
    clarity: Optional[float]
    confidence: Optional[float]
    grammar: Optional[float]
    pronunciation: Optional[float]
    communication: Optional[float]
    overall: Optional[float]
    recommendations: Optional[str]
    scored_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────── Progress / Trend ───────────────

class SessionScoreSummary(BaseModel):
    session_id: int
    session_name: Optional[str]
    started_at: datetime
    fluency: Optional[float]
    clarity: Optional[float]
    confidence: Optional[float]
    grammar: Optional[float]
    pronunciation: Optional[float]
    communication: Optional[float]
    overall: Optional[float]


class StudentProgressResponse(BaseModel):
    student_id: int
    student_name: str
    sessions: List[SessionScoreSummary]


# ─────────────── Upload Response ───────────────

class UploadResponse(BaseModel):
    session_id: int
    audio_id: int
    job_id: str
    message: str
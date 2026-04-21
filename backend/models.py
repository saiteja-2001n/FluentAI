from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    class_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("SpeakerScore", back_populates="student")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, nullable=True)
    session_name = Column(String(255), nullable=True)
    session_type = Column(Enum("discussion", "debate", "individual"), default="discussion")
    status = Column(Enum("recording", "processing", "completed", "failed"), default="recording")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    audio_files = relationship("AudioFile", back_populates="session")
    scores = relationship("SpeakerScore", back_populates="session")


class AudioFile(Base):
    __tablename__ = "audio_files"

    audio_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    duration = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="audio_files")
    segments = relationship("SpeakerSegment", back_populates="audio_file")


class Speaker(Base):
    __tablename__ = "speakers"

    speaker_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    speaker_label = Column(String(100), nullable=False)

    segments = relationship("SpeakerSegment", back_populates="speaker")


class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"

    segment_id = Column(Integer, primary_key=True, index=True)
    audio_id = Column(Integer, ForeignKey("audio_files.audio_id"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.speaker_id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=True)
    text = Column(Text, nullable=True)          # ✅ added — transcript text

    audio_file = relationship("AudioFile", back_populates="segments")
    speaker = relationship("Speaker", back_populates="segments")


class SpeakerScore(Base):
    __tablename__ = "speaker_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    speaker_label = Column(String(50), nullable=False)

    fluency = Column(Float, nullable=True)
    clarity = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    grammar = Column(Float, nullable=True)
    pronunciation = Column(Float, nullable=True)
    communication = Column(Float, nullable=True)
    overall = Column(Float, nullable=True)

    recommendations = Column(Text, nullable=True)
    scored_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="scores")
    session = relationship("Session", back_populates="scores")


    from sqlalchemy import Enum as SQLEnum

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(Integer, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum("pending", "sent", "read"), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
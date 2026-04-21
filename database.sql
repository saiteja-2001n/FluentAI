-- ============================================================
--  Audio Fluency Capture & Analysis System — Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS audio_diarization;
USE audio_diarization;

-- ------------------------------------------------------------
-- 1. USERS
--    Stores both teachers and students.
--    role: 'teacher' | 'student'
-- ------------------------------------------------------------
CREATE TABLE users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(255)        NOT NULL,
    email        VARCHAR(255)        NOT NULL UNIQUE,
    role         ENUM('teacher', 'student') NOT NULL DEFAULT 'student',
    created_at   DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. CLASSROOMS
--    A teacher owns one or more classrooms.
-- ------------------------------------------------------------
CREATE TABLE classrooms (
    classroom_id   INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id     INT          NOT NULL,
    classroom_name VARCHAR(255) NOT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_classroom_teacher
        FOREIGN KEY (teacher_id) REFERENCES users (user_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 3. CLASSROOM_STUDENTS  (many-to-many)
--    Maps students to classrooms.
-- ------------------------------------------------------------
CREATE TABLE classroom_students (
    classroom_id INT NOT NULL,
    student_id   INT NOT NULL,
    joined_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (classroom_id, student_id),

    CONSTRAINT fk_cs_classroom
        FOREIGN KEY (classroom_id) REFERENCES classrooms (classroom_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cs_student
        FOREIGN KEY (student_id) REFERENCES users (user_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 4. SESSIONS
--    One recording session per classroom event (debate, discussion, etc.).
--    status: 'recording' | 'processing' | 'completed' | 'failed'
-- ------------------------------------------------------------
CREATE TABLE sessions (
    session_id    INT AUTO_INCREMENT PRIMARY KEY,
    classroom_id  INT          NOT NULL,
    session_name  VARCHAR(255),
    session_type  ENUM('discussion', 'debate', 'individual') NOT NULL DEFAULT 'discussion',
    status        ENUM('recording', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'recording',
    started_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at      DATETIME,

    CONSTRAINT fk_session_classroom
        FOREIGN KEY (classroom_id) REFERENCES classrooms (classroom_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 5. AUDIO_FILES
--    Each session may have one or more audio files (live chunks or uploads).
-- ------------------------------------------------------------
CREATE TABLE audio_files (
    audio_id    INT AUTO_INCREMENT PRIMARY KEY,
    session_id  INT          NOT NULL,
    file_name   VARCHAR(255) NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    duration    FLOAT,
    uploaded_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audio_session
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 6. SPEAKERS
--    Diarization labels resolved to actual students.
--    speaker_label: raw diarization tag e.g. "SPEAKER_01"
--    user_id: resolved student (nullable until confirmed)
-- ------------------------------------------------------------
CREATE TABLE speakers (
    speaker_id    INT AUTO_INCREMENT PRIMARY KEY,
    session_id    INT          NOT NULL,
    user_id       INT,                          -- NULL until label is confirmed
    speaker_label VARCHAR(100) NOT NULL,

    CONSTRAINT fk_speaker_session
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_speaker_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 7. SEGMENTS
--    Time-coded speech segments per speaker per audio file.
-- ------------------------------------------------------------
CREATE TABLE segments (
    segment_id  INT AUTO_INCREMENT PRIMARY KEY,
    audio_id    INT   NOT NULL,
    speaker_id  INT   NOT NULL,
    start_time  FLOAT NOT NULL,
    end_time    FLOAT NOT NULL,
    duration    FLOAT GENERATED ALWAYS AS (end_time - start_time) STORED,

    CONSTRAINT fk_segment_audio
        FOREIGN KEY (audio_id) REFERENCES audio_files (audio_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_segment_speaker
        FOREIGN KEY (speaker_id) REFERENCES speakers (speaker_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 8. SCORES
--    Per-speaker evaluation scores for each session.
--    All metric columns are 0–100.
-- ------------------------------------------------------------
CREATE TABLE scores (
    score_id              INT AUTO_INCREMENT PRIMARY KEY,
    session_id            INT            NOT NULL,
    speaker_id            INT            NOT NULL,
    pronunciation         DECIMAL(5, 2),   -- 0–100
    fluency               DECIMAL(5, 2),
    clarity               DECIMAL(5, 2),
    confidence            DECIMAL(5, 2),
    grammar               DECIMAL(5, 2),
    overall_communication DECIMAL(5, 2),
    scored_at             DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_score_session
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_score_speaker
        FOREIGN KEY (speaker_id) REFERENCES speakers (speaker_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 9. RECOMMENDATIONS
--    Actionable improvement tips per speaker per session.
-- ------------------------------------------------------------
CREATE TABLE recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id        INT           NOT NULL,
    speaker_id        INT           NOT NULL,
    category          VARCHAR(100),            -- e.g. 'Pronunciation', 'Fluency'
    tip               TEXT          NOT NULL,
    created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rec_session
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_rec_speaker
        FOREIGN KEY (speaker_id) REFERENCES speakers (speaker_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 10. NOTIFICATIONS
--     Alerts sent to users when new reports are available.
--     status: 'pending' | 'sent' | 'read'
-- ------------------------------------------------------------
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NOT NULL,
    session_id      INT,
    message         TEXT         NOT NULL,
    status          ENUM('pending', 'sent', 'read') NOT NULL DEFAULT 'pending',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at         DATETIME,

    CONSTRAINT fk_notif_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notif_session
        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- INDEXES for common query patterns
-- ------------------------------------------------------------

-- Look up all sessions for a classroom
CREATE INDEX idx_sessions_classroom ON sessions (classroom_id);

-- Look up all scores for a student across sessions (trend queries)
CREATE INDEX idx_scores_speaker ON scores (speaker_id, scored_at);

-- Look up segments by audio file
CREATE INDEX idx_segments_audio ON segments (audio_id);

-- Look up notifications by user
CREATE INDEX idx_notifications_user ON notifications (user_id, status);

USE audio_diarization;
ALTER TABLE sessions MODIFY classroom_id INT NULL;


USE audio_diarization;
SHOW TABLES;

DESCRIBE segments;

DESCRIBE scores;

DESCRIBE recommendations;

SELECT * FROM recommendations LIMIT 3;

SELECT * FROM speaker_scores LIMIT 3;

ALTER TABLE speaker_segments ADD COLUMN text TEXT NULL;

USE audio_diarization;
DESCRIBE notifications;

USE audio_diarization;

INSERT INTO users (full_name, email, role)
VALUES ('Test User', 'test@example.com', 'student');

SELECT * FROM users;







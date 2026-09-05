---------------------------------------------------------
-- 01_create_tables.sql
-- Gym Management Database Schema
---------------------------------------------------------

---------------------------------------------------------
-- Sequences (Primary Key Auto-Increment)
---------------------------------------------------------
CREATE SEQUENCE seq_member_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_trainer_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_exercise_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_session_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_log_id START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_payment_id START WITH 1 INCREMENT BY 1 NOCACHE;

---------------------------------------------------------
-- 1. Member
---------------------------------------------------------
CREATE TABLE Member (
    member_id NUMBER PRIMARY KEY,
    name VARCHAR2(50) NOT NULL,
    phone VARCHAR2(20) NOT NULL UNIQUE,
    gender VARCHAR2(1) NOT NULL CHECK (gender IN ('M', 'F')),
    join_date DATE NOT NULL DEFAULT SYSDATE,
    expiry_date DATE NOT NULL,
    remaining_pt_count NUMBER NOT NULL DEFAULT 0 CHECK (remaining_pt_count >= 0),
    created_at DATE DEFAULT SYSDATE
);

---------------------------------------------------------
-- 2. Trainer
---------------------------------------------------------
CREATE TABLE Trainer (
    trainer_id NUMBER PRIMARY KEY,
    name VARCHAR2(50) NOT NULL,
    specialty VARCHAR2(50) NOT NULL,
    career_year NUMBER NOT NULL CHECK (career_year >= 0),
    created_at DATE DEFAULT SYSDATE
);

---------------------------------------------------------
-- 3. Exercise
---------------------------------------------------------
CREATE TABLE Exercise (
    exercise_id NUMBER PRIMARY KEY,
    name VARCHAR2(50) NOT NULL UNIQUE,
    part VARCHAR2(20) NOT NULL,
    created_at DATE DEFAULT SYSDATE
);

---------------------------------------------------------
-- 4. PT_Session
---------------------------------------------------------
CREATE TABLE PT_Session (
    session_id NUMBER PRIMARY KEY,
    member_id NUMBER NOT NULL,
    trainer_id NUMBER NOT NULL,
    session_date DATE NOT NULL,
    session_time VARCHAR2(5) NOT NULL CHECK (REGEXP_LIKE(session_time, '^\d{2}:\d{2}$')),
    status VARCHAR2(20) NOT NULL DEFAULT 'SCHEDULED'
    CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    created_at DATE DEFAULT SYSDATE,
    FOREIGN KEY (member_id) REFERENCES Member (member_id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer (trainer_id),
    UNIQUE (trainer_id, session_date, session_time)
);

---------------------------------------------------------
-- 5. Workout_Log
---------------------------------------------------------
CREATE TABLE Workout_Log (
    log_id NUMBER PRIMARY KEY,
    member_id NUMBER NOT NULL,
    exercise_id NUMBER NOT NULL,
    log_date DATE NOT NULL DEFAULT SYSDATE,
    weight NUMBER CHECK (weight IS NULL OR weight > 0),
    sets NUMBER NOT NULL CHECK (sets > 0),
    reps NUMBER NOT NULL CHECK (reps > 0),
    feedback VARCHAR2(200),
    created_at DATE DEFAULT SYSDATE,
    FOREIGN KEY (member_id) REFERENCES Member (member_id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES Exercise (exercise_id)
);

---------------------------------------------------------
-- 6. Payment
---------------------------------------------------------
CREATE TABLE Payment (
    payment_id NUMBER PRIMARY KEY,
    member_id NUMBER NOT NULL,
    amount NUMBER NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL DEFAULT SYSDATE,
    method VARCHAR2(20) NOT NULL CHECK (method IN ('Card', 'Cash', 'Transfer')),
    category VARCHAR2(20) NOT NULL CHECK (category IN ('PT', 'Membership', 'Visit')),
    created_at DATE DEFAULT SYSDATE,
    FOREIGN KEY (member_id) REFERENCES Member (member_id) ON DELETE CASCADE
);

---------------------------------------------------------
-- Indexes
---------------------------------------------------------
CREATE INDEX idx_pt_session_member ON PT_Session (member_id);
CREATE INDEX idx_pt_session_date ON PT_Session (session_date);
CREATE INDEX idx_workout_member ON Workout_Log (member_id);
CREATE INDEX idx_workout_date ON Workout_Log (log_date);
CREATE INDEX idx_payment_member ON Payment (member_id);
CREATE INDEX idx_member_expiry ON Member (expiry_date);

---------------------------------------------------------
-- Trigger: PT 세션 완료 시 remaining_pt_count 자동 차감
-- noqa: disable=all
---------------------------------------------------------
CREATE OR REPLACE TRIGGER trg_pt_session_complete
AFTER UPDATE OF status ON PT_Session
FOR EACH ROW
BEGIN
    IF :NEW.status = 'COMPLETED' AND :OLD.status != 'COMPLETED' THEN -- noqa
        UPDATE Member
        SET remaining_pt_count = remaining_pt_count - 1
        WHERE member_id = :NEW.member_id -- noqa
            AND remaining_pt_count > 0;
    END IF;
END;
/
-- noqa: enable=all

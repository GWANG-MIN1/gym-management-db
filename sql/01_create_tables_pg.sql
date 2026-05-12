-- =============================================================
-- Gym Management DB — PostgreSQL 15 Schema
-- Oracle XE 21c → PostgreSQL 15 migration
-- Changes:
--   NUMBER          → INTEGER / NUMERIC
--   VARCHAR2(n)     → VARCHAR(n)
--   SYSDATE         → CURRENT_DATE
--   REGEXP_LIKE()   → col ~ 'pattern'
--   NUMBER PK       → INTEGER GENERATED ALWAYS AS IDENTITY
-- =============================================================

CREATE TABLE Member (
    member_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               VARCHAR(50)  NOT NULL,
    phone              VARCHAR(20)  NOT NULL UNIQUE,
    gender             VARCHAR(1)   NOT NULL CHECK (gender IN ('M', 'F')),
    join_date          DATE         NOT NULL DEFAULT CURRENT_DATE,
    expiry_date        DATE         NOT NULL,
    remaining_pt_count INTEGER      NOT NULL DEFAULT 0 CHECK (remaining_pt_count >= 0),
    created_at         DATE         DEFAULT CURRENT_DATE
);

CREATE TABLE Trainer (
    trainer_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    specialty   VARCHAR(50) NOT NULL,
    career_year INTEGER     NOT NULL CHECK (career_year >= 0),
    created_at  DATE        DEFAULT CURRENT_DATE
);

CREATE TABLE Exercise (
    exercise_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    part        VARCHAR(20) NOT NULL,
    created_at  DATE        DEFAULT CURRENT_DATE
);

CREATE TABLE PT_Session (
    session_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id    INTEGER     NOT NULL,
    trainer_id   INTEGER     NOT NULL,
    session_date DATE        NOT NULL,
    session_time VARCHAR(5)  NOT NULL CHECK (session_time ~ '^\d{2}:\d{2}$'),
    status       VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
                             CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    created_at   DATE        DEFAULT CURRENT_DATE,
    FOREIGN KEY (member_id)  REFERENCES Member(member_id)  ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id),
    UNIQUE (trainer_id, session_date, session_time)
);

CREATE TABLE Workout_Log (
    log_id      INTEGER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id   INTEGER        NOT NULL,
    exercise_id INTEGER        NOT NULL,
    log_date    DATE           NOT NULL DEFAULT CURRENT_DATE,
    weight      NUMERIC(6, 2)  CHECK (weight IS NULL OR weight > 0),
    sets        INTEGER        NOT NULL CHECK (sets > 0),
    reps        INTEGER        NOT NULL CHECK (reps > 0),
    feedback    VARCHAR(200),
    created_at  DATE           DEFAULT CURRENT_DATE,
    FOREIGN KEY (member_id)   REFERENCES Member(member_id)   ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES Exercise(exercise_id)
);

CREATE TABLE Payment (
    payment_id   INTEGER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id    INTEGER        NOT NULL,
    amount       NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    payment_date DATE           NOT NULL DEFAULT CURRENT_DATE,
    method       VARCHAR(20)    NOT NULL CHECK (method IN ('Card', 'Cash', 'Transfer')),
    category     VARCHAR(20)    NOT NULL CHECK (category IN ('PT', 'Membership', 'Visit')),
    created_at   DATE           DEFAULT CURRENT_DATE,
    FOREIGN KEY (member_id) REFERENCES Member(member_id) ON DELETE CASCADE
);

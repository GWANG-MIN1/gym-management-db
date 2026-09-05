-- =============================================================
-- Gym Management DB — PostgreSQL 15 Schema
-- Oracle XE 21c → PostgreSQL 15 migration
-- Changes:
--   NUMBER          → INTEGER / NUMERIC
--   VARCHAR2(n)     → VARCHAR(n)
--   SYSDATE         → CURRENT_DATE
--   REGEXP_LIKE()   → col ~ 'pattern'
--   NUMBER PK       → INTEGER GENERATED ALWAYS AS IDENTITY
--
-- 이 파일은 api/models.py 의 SQLAlchemy 모델, api/migrations 의 마이그레이션 결과와
-- 1:1로 대응합니다(테이블 6개 / 제약 / 인덱스 동일 — 어긋나면 api/tests 에서 잡힙니다).
-- 로컬 docker compose 초기화용이고, 배포 환경 스키마는 마이그레이션이 적용합니다.
--
-- Oracle 버전에 있던 trg_pt_session_complete 트리거(PT 완료 시 잔여 횟수 차감)는
-- 이식하지 않았습니다. 차감은 API(PATCH /sessions/{id}/complete)에서 트랜잭션으로
-- 처리하며, 트리거를 함께 두면 로컬(SQL 파일로 초기화)과 배포(마이그레이션) 환경에서
-- 차감이 두 번 일어나 결과가 달라지기 때문입니다.
-- =============================================================

CREATE TABLE Member (
    member_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               VARCHAR(50)  NOT NULL,
    phone              VARCHAR(20)  NOT NULL UNIQUE,
    gender             VARCHAR(1)   NOT NULL,
    join_date          DATE         NOT NULL DEFAULT CURRENT_DATE,
    expiry_date        DATE         NOT NULL,
    remaining_pt_count INTEGER      NOT NULL DEFAULT 0,
    created_at         DATE         DEFAULT CURRENT_DATE,
    -- 제약 이름은 api/models.py 와 동일하게 지정한다.
    -- API(api/errors.py)가 이 이름으로 사용자용 오류 메시지를 고르기 때문에,
    -- 이름이 환경마다 다르면 같은 위반에 다른 응답이 나간다.
    CONSTRAINT ck_member_gender CHECK (gender IN ('M', 'F')),
    CONSTRAINT ck_member_pt_count CHECK (remaining_pt_count >= 0)
);

CREATE TABLE Trainer (
    trainer_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    specialty   VARCHAR(50) NOT NULL,
    career_year INTEGER     NOT NULL,
    created_at  DATE        DEFAULT CURRENT_DATE,
    CONSTRAINT ck_trainer_career CHECK (career_year >= 0)
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
    session_time VARCHAR(5)  NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    created_at   DATE        DEFAULT CURRENT_DATE,
    -- 00:00 ~ 23:59 만 허용 (기존 '^\d{2}:\d{2}$' 는 '99:99' 도 통과했음)
    CONSTRAINT ck_session_time_format
    CHECK (session_time ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
    CONSTRAINT ck_session_status
    CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT fk_pt_session_member FOREIGN KEY (member_id)
    REFERENCES Member (member_id) ON DELETE CASCADE,
    CONSTRAINT fk_pt_session_trainer FOREIGN KEY (trainer_id)
    REFERENCES Trainer (trainer_id)
);

-- 같은 트레이너 / 같은 회원의 같은 날짜·시간 중복 예약 차단 (API 는 이 위반을 409 로 변환).
-- 취소(CANCELLED)된 예약은 슬롯을 비워야 하므로 부분 유니크 인덱스를 사용합니다.
CREATE UNIQUE INDEX uq_trainer_slot
ON PT_Session (trainer_id, session_date, session_time)
WHERE status <> 'CANCELLED';

CREATE UNIQUE INDEX uq_member_slot
ON PT_Session (member_id, session_date, session_time)
WHERE status <> 'CANCELLED';

CREATE TABLE Workout_Log (
    log_id      INTEGER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id   INTEGER        NOT NULL,
    exercise_id INTEGER        NOT NULL,
    log_date    DATE           NOT NULL DEFAULT CURRENT_DATE,
    weight      NUMERIC(6, 2),
    sets        INTEGER        NOT NULL,
    reps        INTEGER        NOT NULL,
    feedback    VARCHAR(200),
    created_at  DATE           DEFAULT CURRENT_DATE,
    CONSTRAINT ck_workout_weight CHECK (weight IS NULL OR weight > 0),
    CONSTRAINT ck_workout_sets CHECK (sets > 0),
    CONSTRAINT ck_workout_reps CHECK (reps > 0),
    CONSTRAINT fk_workout_member FOREIGN KEY (member_id)
    REFERENCES Member (member_id) ON DELETE CASCADE,
    CONSTRAINT fk_workout_exercise FOREIGN KEY (exercise_id)
    REFERENCES Exercise (exercise_id)
);

CREATE TABLE Payment (
    payment_id   INTEGER        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id    INTEGER        NOT NULL,
    amount       NUMERIC(10, 2) NOT NULL,
    payment_date DATE           NOT NULL DEFAULT CURRENT_DATE,
    method       VARCHAR(20)    NOT NULL,
    category     VARCHAR(20)    NOT NULL,
    created_at   DATE           DEFAULT CURRENT_DATE,
    CONSTRAINT ck_payment_amount CHECK (amount > 0),
    CONSTRAINT ck_payment_method CHECK (method IN ('Card', 'Cash', 'Transfer')),
    CONSTRAINT ck_payment_category CHECK (category IN ('PT', 'Membership', 'Visit')),
    CONSTRAINT fk_payment_member FOREIGN KEY (member_id)
    REFERENCES Member (member_id) ON DELETE CASCADE
);

-- =============================================================
-- Indexes — FK 컬럼과 조회 조건 컬럼
-- (PK / UNIQUE 는 PostgreSQL 이 인덱스를 자동 생성하므로 제외.
--  PT_Session.member_id / trainer_id 는 위 유니크 인덱스의 선두 컬럼이라 별도 인덱스 불필요)
-- =============================================================
CREATE INDEX idx_member_expiry ON Member (expiry_date);
CREATE INDEX idx_pt_session_date ON PT_Session (session_date);
CREATE INDEX idx_workout_member ON Workout_Log (member_id);
CREATE INDEX idx_workout_date ON Workout_Log (log_date);
CREATE INDEX idx_payment_member ON Payment (member_id);

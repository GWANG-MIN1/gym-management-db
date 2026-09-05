-- 이전 버전(1b688ce)의 api/models.py 가 create_all() 로 만들던 스키마.
-- 운영 DB 가 이 상태이므로, 마이그레이션이 여기서 현재 스키마로 올라가는지 검증한다.
--   * created_at 이 NOT NULL 인데 기본값이 없다  → 현재 API 의 등록 요청이 전부 실패
--   * uq_trainer_slot 이 일반 UNIQUE 제약이다     → 취소한 예약의 시간대를 다시 못 씀
--   * PK 가 SERIAL, 운동/운동기록/결제 테이블 없음

CREATE TABLE member (
    member_id SERIAL NOT NULL,
    name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    gender VARCHAR(1) NOT NULL,
    join_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    remaining_pt_count INTEGER NOT NULL,
    created_at DATE NOT NULL,
    CONSTRAINT member_pkey PRIMARY KEY (member_id),
    CONSTRAINT ck_member_gender CHECK (gender IN ('M', 'F')),
    CONSTRAINT ck_member_pt_count CHECK (remaining_pt_count >= 0),
    CONSTRAINT member_phone_key UNIQUE (phone)
);

CREATE TABLE trainer (
    trainer_id SERIAL NOT NULL,
    name VARCHAR(50) NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    career_year INTEGER NOT NULL,
    created_at DATE NOT NULL,
    CONSTRAINT trainer_pkey PRIMARY KEY (trainer_id),
    CONSTRAINT ck_trainer_career CHECK (career_year >= 0)
);

CREATE TABLE pt_session (
    session_id SERIAL NOT NULL,
    member_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    session_date DATE NOT NULL,
    session_time VARCHAR(5) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATE NOT NULL,
    CONSTRAINT pt_session_pkey PRIMARY KEY (session_id),
    CONSTRAINT ck_session_status
        CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    CONSTRAINT uq_trainer_slot UNIQUE (trainer_id, session_date, session_time),
    CONSTRAINT pt_session_member_id_fkey FOREIGN KEY (member_id)
        REFERENCES member (member_id) ON DELETE CASCADE,
    CONSTRAINT pt_session_trainer_id_fkey FOREIGN KEY (trainer_id)
        REFERENCES trainer (trainer_id)
);

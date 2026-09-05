-- =============================================================
-- Gym Management DB — PostgreSQL 샘플 데이터
--
-- 루트의 02_insert_sample_data.sql 은 Oracle 전용이라
-- PostgreSQL 에 그대로 넣을 수 없습니다.
--   SYSDATE                → CURRENT_DATE
--   PK 직접 지정 (1, 2, …) → GENERATED ALWAYS AS IDENTITY 라 지정 불가
--                            (직접 넣으면 시퀀스가 밀려 이후 INSERT 가 충돌)
-- 그래서 PK 는 DB 가 채우게 두고, FK 는 UNIQUE 값(phone / 이름)으로 조회해 연결합니다.
--
-- docker compose up 시 01_create_tables_pg.sql 다음에 자동 실행됩니다.
-- =============================================================

-- ── Member (10 rows) ─────────────────────────────────────────
INSERT INTO Member (name, phone, gender, join_date, expiry_date, remaining_pt_count)
VALUES
('Kim Cheol-Su', '010-1111-2221', 'M', DATE '2025-01-01', DATE '2025-12-31', 5),
('Hong Gil-Dong', '010-2222-3333', 'M', DATE '2025-02-10', DATE '2026-02-10', 8),
('Lee Young-Hee', '010-3333-4444', 'F', DATE '2025-01-20', DATE '2025-11-30', 3),
('Park Min-Su', '010-4444-5555', 'M', DATE '2025-03-01', DATE '2026-03-01', 12),
('Choi Ye-Ri', '010-5555-6666', 'F', DATE '2025-02-18', DATE '2026-02-18', 6),
('Jung Woo-Sung', '010-6666-7777', 'M', DATE '2025-01-05', DATE '2025-12-31', 0),
('Song Ha-Neul', '010-7777-8888', 'F', DATE '2025-03-10', DATE '2026-03-10', 9),
('Han Ji-Min', '010-8888-9999', 'F', DATE '2025-02-01', DATE '2026-02-01', 4),
('Jang Woo-Hyuk', '010-9999-1111', 'M', DATE '2025-01-12', DATE '2025-12-12', 7),
('Oh Tae-Sik', '010-1212-3434', 'M', DATE '2025-03-05', DATE '2026-03-05', 2);

-- ── Trainer (10 rows) ────────────────────────────────────────
INSERT INTO Trainer (name, specialty, career_year)
VALUES
('Trainer Kim', 'Chest', 5),
('Trainer Park', 'Back', 7),
('Trainer Lee', 'Leg', 3),
('Trainer Jung', 'Shoulder', 4),
('Trainer Choi', 'Arm', 6),
('Trainer Yoon', 'Pilates', 2),
('Trainer Han', 'Crossfit', 8),
('Trainer Oh', 'Core', 4),
('Trainer Hong', 'Full Body', 10),
('Trainer Kang', 'HIIT', 1);

-- ── Exercise (10 rows) ───────────────────────────────────────
INSERT INTO Exercise (name, part)
VALUES
('Bench Press', 'Chest'),
('Squat', 'Leg'),
('Deadlift', 'Back'),
('Shoulder Press', 'Shoulder'),
('Lat Pulldown', 'Back'),
('Plank', 'Core'),
('Leg Press', 'Leg'),
('Dumbbell Curl', 'Arm'),
('Cable Pushdown', 'Arm'),
('Burpee', 'Full Body');

-- ── PT_Session (13 rows) ─────────────────────────────────────
INSERT INTO PT_Session (member_id, trainer_id, session_date, session_time, status)
SELECT
    m.member_id,
    t.trainer_id,
    v.session_date::DATE,
    v.session_time,
    v.status
FROM (
    VALUES
    ('010-1111-2221', 'Trainer Kim', '2025-03-10', '10:00', 'COMPLETED'),
    ('010-1111-2221', 'Trainer Kim', '2025-03-17', '10:00', 'COMPLETED'),
    ('010-2222-3333', 'Trainer Park', '2025-03-12', '14:00', 'COMPLETED'),
    ('010-3333-4444', 'Trainer Lee', '2025-03-15', '09:00', 'CANCELLED'),
    ('010-4444-5555', 'Trainer Jung', '2025-03-20', '11:00', 'SCHEDULED'),
    ('010-5555-6666', 'Trainer Choi', '2025-03-08', '13:00', 'COMPLETED'),
    ('010-6666-7777', 'Trainer Yoon', '2025-03-21', '16:00', 'SCHEDULED'),
    ('010-7777-8888', 'Trainer Han', '2025-03-22', '15:00', 'COMPLETED'),
    ('010-8888-9999', 'Trainer Oh', '2025-03-25', '17:00', 'SCHEDULED'),
    ('010-9999-1111', 'Trainer Hong', '2025-03-11', '10:30', 'COMPLETED'),
    ('010-1111-2221', 'Trainer Kim', '2025-03-01', '09:00', 'COMPLETED'),
    ('010-1111-2221', 'Trainer Kim', '2025-03-25', '11:00', 'SCHEDULED'),
    ('010-1111-2221', 'Trainer Kim', '2025-04-02', '14:00', 'COMPLETED')
) AS v (phone, trainer_name, session_date, session_time, status)
INNER JOIN Member AS m ON v.phone = m.phone
INNER JOIN Trainer AS t ON v.trainer_name = t.name;

-- ── Workout_Log (10 rows) ────────────────────────────────────
INSERT INTO Workout_Log (member_id, exercise_id, log_date, weight, sets, reps, feedback)
SELECT
    m.member_id,
    e.exercise_id,
    v.log_date::DATE,
    v.weight::NUMERIC,
    v.sets::INTEGER,
    v.reps::INTEGER,
    v.feedback
FROM (
    VALUES
    ('010-1111-2221', 'Bench Press', '2025-03-10', '60', '5', '10', 'Good form'),
    ('010-1111-2221', 'Squat', '2025-03-10', '80', '5', '8', 'Tough but successful'),
    ('010-2222-3333', 'Deadlift', '2025-03-12', '70', '4', '6', 'Good back engagement'),
    ('010-3333-4444', 'Shoulder Press', '2025-03-15', '15', '4', '12', 'Stable shoulder movement'),
    ('010-4444-5555', 'Lat Pulldown', '2025-03-20', '50', '4', '10', 'Good'),
    ('010-5555-6666', 'Plank', '2025-03-08', NULL, '3', '1', 'Core activation achieved'),
    ('010-6666-7777', 'Leg Press', '2025-03-21', '180', '5', '10', 'High intensity'),
    ('010-7777-8888', 'Dumbbell Curl', '2025-03-22', '12', '3', '15', 'Good arm pump'),
    ('010-8888-9999', 'Cable Pushdown', '2025-03-25', '25', '4', '12', 'Good tricep activation'),
    ('010-9999-1111', 'Burpee', '2025-03-11', NULL, '1', '20', 'Full-body workout')
) AS v (phone, exercise_name, log_date, weight, sets, reps, feedback)
INNER JOIN Member AS m ON v.phone = m.phone
INNER JOIN Exercise AS e ON v.exercise_name = e.name;

-- ── Payment (10 rows) ────────────────────────────────────────
INSERT INTO Payment (member_id, amount, payment_date, method, category)
SELECT
    m.member_id,
    v.amount::NUMERIC,
    v.payment_date::DATE,
    v.method,
    v.category
FROM (
    VALUES
    ('010-1111-2221', '500000', '2025-01-05', 'Card', 'PT'),
    ('010-2222-3333', '700000', '2025-02-11', 'Card', 'PT'),
    ('010-3333-4444', '150000', '2025-01-20', 'Cash', 'Membership'),
    ('010-4444-5555', '800000', '2025-03-01', 'Card', 'PT'),
    ('010-5555-6666', '120000', '2025-02-18', 'Cash', 'Membership'),
    ('010-6666-7777', '50000', '2025-01-10', 'Card', 'Visit'),
    ('010-7777-8888', '900000', '2025-03-10', 'Card', 'PT'),
    ('010-8888-9999', '130000', '2025-02-01', 'Cash', 'Membership'),
    ('010-9999-1111', '550000', '2025-01-12', 'Card', 'PT'),
    ('010-1212-3434', '30000', '2025-03-05', 'Cash', 'Visit')
) AS v (phone, amount, payment_date, method, category)
INNER JOIN Member AS m ON v.phone = m.phone;

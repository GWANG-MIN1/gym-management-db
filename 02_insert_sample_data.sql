---------------------------------------------------------
-- 02_insert_sample_data.sql
-- Sample data for Gym Management Database Project
-- Inserts 10 rows per table (+ 추가 PT_Session 3 rows)
---------------------------------------------------------

---------------------------------------------------------
-- Member (10 rows)
---------------------------------------------------------
INSERT INTO Member VALUES (1, '김철수', '010-1111-2221', 'M', DATE '2025-01-01', DATE '2025-12-31', 5);
INSERT INTO Member VALUES (2, '홍길동', '010-2222-3333', 'M', DATE '2025-02-10', DATE '2026-02-10', 8);
INSERT INTO Member VALUES (3, '이영희', '010-3333-4444', 'F', DATE '2025-01-20', DATE '2025-11-30', 3);
INSERT INTO Member VALUES (4, '박민수', '010-4444-5555', 'M', DATE '2025-03-01', DATE '2026-03-01', 12);
INSERT INTO Member VALUES (5, '최예린', '010-5555-6666', 'F', DATE '2025-02-18', DATE '2026-02-18', 6);
INSERT INTO Member VALUES (6, '정우성', '010-6666-7777', 'M', DATE '2025-01-05', DATE '2025-12-31', 0);
INSERT INTO Member VALUES (7, '송하늘', '010-7777-8888', 'F', DATE '2025-03-10', DATE '2026-03-10', 9);
INSERT INTO Member VALUES (8, '한지민', '010-8888-9999', 'F', DATE '2025-02-01', DATE '2026-02-01', 4);
INSERT INTO Member VALUES (9, '장우혁', '010-9999-1111', 'M', DATE '2025-01-12', DATE '2025-12-12', 7);
INSERT INTO Member VALUES (10, '오태식', '010-1212-3434', 'M', DATE '2025-03-05', DATE '2026-03-05', 2);

---------------------------------------------------------
-- Trainer (10 rows)
---------------------------------------------------------
INSERT INTO Trainer VALUES (1, '김트레이너', 'Chest', 5);
INSERT INTO Trainer VALUES (2, '박트레이너', 'Back', 7);
INSERT INTO Trainer VALUES (3, '이트레이너', 'Leg', 3);
INSERT INTO Trainer VALUES (4, '정트레이너', 'Shoulder', 4);
INSERT INTO Trainer VALUES (5, '최트레이너', 'Arm', 6);
INSERT INTO Trainer VALUES (6, '윤트레이너', 'Pilates', 2);
INSERT INTO Trainer VALUES (7, '한트레이너', 'Crossfit', 8);
INSERT INTO Trainer VALUES (8, '오트레이너', 'Core', 4);
INSERT INTO Trainer VALUES (9, '홍트레이너', 'Full Body', 10);
INSERT INTO Trainer VALUES (10, '강트레이너', 'HIIT', 1);

---------------------------------------------------------
-- Exercise (10 rows)
---------------------------------------------------------
INSERT INTO Exercise VALUES (1, '벤치프레스', 'Chest');
INSERT INTO Exercise VALUES (2, '스쿼트', 'Leg');
INSERT INTO Exercise VALUES (3, '데드리프트', 'Back');
INSERT INTO Exercise VALUES (4, '숄더프레스', 'Shoulder');
INSERT INTO Exercise VALUES (5, '랫풀다운', 'Back');
INSERT INTO Exercise VALUES (6, '플랭크', 'Core');
INSERT INTO Exercise VALUES (7, '레그프레스', 'Leg');
INSERT INTO Exercise VALUES (8, '덤벨컬', 'Arm');
INSERT INTO Exercise VALUES (9, '케이블푸시다운', 'Arm');
INSERT INTO Exercise VALUES (10, '버피', 'Full Body');

---------------------------------------------------------
-- PT_Session (10 rows +  3 rows = 13 rows)
---------------------------------------------------------
INSERT INTO PT_Session VALUES (1, 1, 1, DATE '2025-03-10', '10:00', 'Completed');
INSERT INTO PT_Session VALUES (2, 1, 1, DATE '2025-03-17', '10:00', 'Completed');
INSERT INTO PT_Session VALUES (3, 2, 2, DATE '2025-03-12', '14:00', 'Completed');
INSERT INTO PT_Session VALUES (4, 3, 3, DATE '2025-03-15', '09:00', 'Canceled');
INSERT INTO PT_Session VALUES (5, 4, 4, DATE '2025-03-20', '11:00', 'Scheduled');
INSERT INTO PT_Session VALUES (6, 5, 5, DATE '2025-03-08', '13:00', 'Completed');
INSERT INTO PT_Session VALUES (7, 6, 6, DATE '2025-03-21', '16:00', 'Scheduled');
INSERT INTO PT_Session VALUES (8, 7, 7, DATE '2025-03-22', '15:00', 'Completed');
INSERT INTO PT_Session VALUES (9, 8, 8, DATE '2025-03-25', '17:00', 'Scheduled');
INSERT INTO PT_Session VALUES (10, 9, 9, DATE '2025-03-11', '10:30', 'Completed');
INSERT INTO PT_Session VALUES (11, 1, 1, DATE '2025-03-01', '09:00', 'Completed');
INSERT INTO PT_Session VALUES (12, 1, 1, DATE '2025-03-25', '11:00', 'Scheduled');
INSERT INTO PT_Session VALUES (13, 1, 1, DATE '2025-04-02', '14:00', 'Completed');

---------------------------------------------------------
-- Workout_Log (10 rows)
---------------------------------------------------------
INSERT INTO Workout_Log VALUES (1, 1, 1, DATE '2025-03-10', 60, 5, 10, '폼 좋음');
INSERT INTO Workout_Log VALUES (2, 1, 2, DATE '2025-03-10', 80, 5, 8, '힘들었지만 성공');
INSERT INTO Workout_Log VALUES (3, 2, 3, DATE '2025-03-12', 70, 4, 6, '등 자극 OK');
INSERT INTO Workout_Log VALUES (4, 3, 4, DATE '2025-03-15', 15, 4, 12, '어깨 안정적');
INSERT INTO Workout_Log VALUES (5, 4, 5, DATE '2025-03-20', 50, 4, 10, '좋음');
INSERT INTO Workout_Log VALUES (6, 5, 6, DATE '2025-03-08', NULL, 3, 1, '코어 강화');
INSERT INTO Workout_Log VALUES (7, 6, 7, DATE '2025-03-21', 180, 5, 10, '강도 높음');
INSERT INTO Workout_Log VALUES (8, 7, 8, DATE '2025-03-22', 12, 3, 15, '팔 펌핑');
INSERT INTO Workout_Log VALUES (9, 8, 9, DATE '2025-03-25', 25, 4, 12, '삼두 자극 OK');
INSERT INTO Workout_Log VALUES (10, 9, 10, DATE '2025-03-11', NULL, 1, 20, '전신 운동');

---------------------------------------------------------
-- Payment (10 rows)
---------------------------------------------------------
INSERT INTO Payment VALUES (1, 1, 500000, DATE '2025-01-05', 'Card', 'PT');
INSERT INTO Payment VALUES (2, 2, 700000, DATE '2025-02-11', 'Card', 'PT');
INSERT INTO Payment VALUES (3, 3, 150000, DATE '2025-01-20', 'Cash', 'Membership');
INSERT INTO Payment VALUES (4, 4, 800000, DATE '2025-03-01', 'Card', 'PT');
INSERT INTO Payment VALUES (5, 5, 120000, DATE '2025-02-18', 'Cash', 'Membership');
INSERT INTO Payment VALUES (6, 6, 50000, DATE '2025-01-10', 'Card', 'Visit');
INSERT INTO Payment VALUES (7, 7, 900000, DATE '2025-03-10', 'Card', 'PT');
INSERT INTO Payment VALUES (8, 8, 130000, DATE '2025-02-01', 'Cash', 'Membership');
INSERT INTO Payment VALUES (9, 9, 550000, DATE '2025-01-12', 'Card', 'PT');
INSERT INTO Payment VALUES (10, 10, 30000, DATE '2025-03-05', 'Cash', 'Visit');

---------------------------------------------------------
COMMIT;
---------------------------------------------------------

---------------------------------------------------------
-- 03_project_queries.sql
-- Demonstration Queries for the Gym Management DB Project
---------------------------------------------------------

---------------------------------------------------------
-- 1. Retrieve all PT sessions for the member named 'Kim Cheol-Su'
---------------------------------------------------------
SELECT
    M.name AS member_name,
    T.name AS trainer_name,
    S.session_date,
    S.session_time,
    S.status
FROM PT_Session AS S
JOIN Member AS M ON S.member_id = M.member_id
JOIN Trainer AS T ON S.trainer_id = T.trainer_id
WHERE M.name = 'Kim Cheol-Su';


---------------------------------------------------------
-- 2. Sort the result of Query (1) by PT session date
---------------------------------------------------------
SELECT
    M.name AS member_name,
    T.name AS trainer_name,
    S.session_date,
    S.session_time,
    S.status
FROM PT_Session AS S
JOIN Member AS M ON S.member_id = M.member_id
JOIN Trainer AS T ON S.trainer_id = T.trainer_id
WHERE M.name = 'Kim Cheol-Su'
ORDER BY S.session_date;


---------------------------------------------------------
-- 3. Retrieve all workout logs for 'Kim Cheol-Su' within the last 30 days
--    (동적 날짜: 항상 현재 날짜 기준으로 계산)
---------------------------------------------------------
SELECT
    W.log_date,
    E.name AS exercise_name,
    W.weight,
    W.sets,
    W.reps,
    W.feedback
FROM Workout_Log AS W
JOIN Exercise AS E ON W.exercise_id = E.exercise_id
WHERE W.member_id = (
    SELECT M.member_id
    FROM Member AS M
    WHERE M.name = 'Kim Cheol-Su'
)
AND W.log_date >= SYSDATE - 30;


---------------------------------------------------------
-- 4. Retrieve all payment records of the member 'Kim Cheol-Su'
---------------------------------------------------------
SELECT
    M.name AS member_name,
    P.amount,
    P.payment_date,
    P.method,
    P.category
FROM Payment AS P
JOIN Member AS M ON P.member_id = M.member_id
WHERE M.name = 'Kim Cheol-Su';


---------------------------------------------------------
-- 5. Retrieve the member whose PT expiry date is the closest upcoming date
---------------------------------------------------------
SELECT
    name,
    phone,
    expiry_date
FROM Member
WHERE expiry_date >= SYSDATE
ORDER BY expiry_date ASC
FETCH FIRST 1 ROW ONLY;


---------------------------------------------------------
-- 6. 트레이너별 완료된 PT 세션 수 및 담당 회원 수
---------------------------------------------------------
SELECT
    T.name AS trainer_name,
    T.specialty,
    COUNT(S.session_id) AS completed_sessions,
    COUNT(DISTINCT S.member_id) AS total_members
FROM Trainer AS T
LEFT JOIN PT_Session AS S
    ON
        T.trainer_id = S.trainer_id
        AND S.status = 'COMPLETED'
GROUP BY T.trainer_id, T.name, T.specialty
ORDER BY completed_sessions DESC;


---------------------------------------------------------
-- 7. PT 잔여 횟수가 3회 이하인 만료 임박 회원 목록
---------------------------------------------------------
SELECT
    name,
    phone,
    expiry_date,
    remaining_pt_count
FROM Member
WHERE
    remaining_pt_count <= 3
    AND expiry_date >= SYSDATE
ORDER BY remaining_pt_count ASC, expiry_date ASC;

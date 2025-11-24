---------------------------------------------------------
-- 03_demo_queries.sql
-- Demonstration Queries for the Gym Management DB Project
-- Used for the 2-minute video demonstration
---------------------------------------------------------

---------------------------------------------------------
-- 1. Retrieve all PT sessions for the member named 'Kim Cheol-Su'
---------------------------------------------------------
SELECT M.name AS member_name,
       T.name AS trainer_name,
       S.session_date,
       S.session_time,
       S.status
FROM PT_Session S
JOIN Member M ON S.member_id = M.member_id
JOIN Trainer T ON S.trainer_id = T.trainer_id
WHERE M.name = 'Kim Cheol-Su';


---------------------------------------------------------
-- 2. Sort the result of Query (1) by PT session date
---------------------------------------------------------
SELECT M.name AS member_name,
       T.name AS trainer_name,
       S.session_date,
       S.session_time,
       S.status
FROM PT_Session S
JOIN Member M ON S.member_id = M.member_id
JOIN Trainer T ON S.trainer_id = T.trainer_id
WHERE M.name = 'Kim Cheol-Su'
ORDER BY S.session_date;


---------------------------------------------------------
-- 3. Retrieve all workout logs for 'Kim Cheol-Su' within the last month
-- (Based on sample data dates)
---------------------------------------------------------
SELECT W.log_date,
       E.name AS exercise_name,
       W.weight,
       W.sets,
       W.reps,
       W.feedback
FROM Workout_Log W
JOIN Exercise E ON W.exercise_id = E.exercise_id
WHERE W.member_id = (
        SELECT member_id 
        FROM Member 
        WHERE name = 'Kim Cheol-Su'
      )
AND W.log_date >= DATE '2025-03-01';  
-- Adjusted to match sample data timeline


---------------------------------------------------------
-- 4. Retrieve all payment records of the member 'Kim Cheol-Su'
---------------------------------------------------------
SELECT M.name AS member_name,
       P.amount,
       P.payment_date,
       P.method,
       P.category
FROM Payment P
JOIN Member M ON P.member_id = M.member_id
WHERE M.name = 'Kim Cheol-Su';


---------------------------------------------------------
-- 5. Retrieve the member whose PT expiry date is the closest upcoming date
-- Based on the CURRENT_DATE (2025-11-24)
---------------------------------------------------------
SELECT name,
phone,
expiry_date
FROM Member
WHERE expiry_date = (
SELECT MIN(expiry_date)
FROM Member
WHERE expiry_date >= CURRENT_DATE
);

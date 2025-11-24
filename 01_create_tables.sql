-- 1. Member
CREATE TABLE Member (
    member_id NUMBER PRIMARY KEY,
    name VARCHAR2(50),
    phone VARCHAR2(20),
    gender VARCHAR2(10),
    join_date DATE,
    expiry_date DATE,
    remaining_pt_count NUMBER
);

-- 2. Trainer
CREATE TABLE Trainer (
    trainer_id NUMBER PRIMARY KEY,
    name VARCHAR2(50),
    specialty VARCHAR2(50),
    career_year NUMBER
);

-- 3. Exercise
CREATE TABLE Exercise (
    exercise_id NUMBER PRIMARY KEY,
    name VARCHAR2(50),
    part VARCHAR2(20)
);

-- 4. PT_Session
CREATE TABLE PT_Session (
    session_id NUMBER PRIMARY KEY,
    member_id NUMBER,
    trainer_id NUMBER,
    session_date DATE,
    session_time VARCHAR2(10),
    status VARCHAR2(20),
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (trainer_id) REFERENCES Trainer(trainer_id)
);

-- 5. Workout_Log
CREATE TABLE Workout_Log (
    log_id NUMBER PRIMARY KEY,
    member_id NUMBER,
    exercise_id NUMBER,
    log_date DATE,
    weight NUMBER,
    sets NUMBER,
    reps NUMBER,
    feedback VARCHAR2(200),
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (exercise_id) REFERENCES Exercise(exercise_id)
);

-- 6. Payment
CREATE TABLE Payment (
    payment_id NUMBER PRIMARY KEY,
    member_id NUMBER,
    amount NUMBER,
    payment_date DATE,
    method VARCHAR2(20),
    category VARCHAR2(20),
    FOREIGN KEY (member_id) REFERENCES Member(member_id)
);

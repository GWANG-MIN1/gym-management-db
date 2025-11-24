# 🏋️‍♂️ Fitness Center Management System
**Gwangmin Park**

---

## 📌 Project Overview
This project aims to design a database system capable of managing **gym members, PT (Personal Training) reservations, and workout logs**.

The system stores and manages various types of data generated in a fitness center, such as:
- Member information  
- Trainer assignments  
- PT reservation schedules  
- Workout records  
- Payment information  

To support efficient management, an **E-R diagram** and **relational schema** were constructed.

---

## ✔ Functional Requirements
1. Administrators must be able to register, edit, and delete member information.  
2. Members must be able to reserve PT sessions with specific trainers.  
3. One trainer must be able to train multiple members.  
4. Members must be able to record workout results (date, exercise type, sets, weight, etc.).  
5. PT reservations must be managed by date and time.  
6. Members must be able to make multiple PT payments, and all payment history must be stored.

---

## ✔ Non-Functional Requirements
1. The system must maintain **data integrity**.  
2. The schema must minimize data redundancy through **normalization**.  
3. Every entity must include a **primary key**.  
4. Referential integrity must be preserved on deletion and modification.

---

## 📘 Entities (Summary)

### **1. Member**
- member_id (PK)  
- name  
- phone  
- gender  
- join_date  
- expiry_date  
- remaining_pt_count  

### **2. Trainer**
- trainer_id (PK)  
- name  
- specialty  
- career_year  

### **3. PT_Session**
- session_id (PK)  
- member_id (FK → Member.member_id)  
- trainer_id (FK → Trainer.trainer_id)  
- session_date  
- session_time  
- status  

### **4. Exercise**
- exercise_id (PK)  
- name  
- part  

### **5. Workout_Log**
- log_id (PK)  
- member_id (FK → Member.member_id)  
- exercise_id (FK → Exercise.exercise_id)  
- log_date  
- weight  
- sets  
- reps  
- feedback  

### **6. Payment**
- payment_id (PK)  
- member_id (FK → Member.member_id)  
- amount  
- payment_date  
- method  
- category  

---

## 🔗 Relationship Summary

### **Trainer — PT_Session**
- Relationship: **1 : N**
- One trainer can conduct PT sessions for many members.  
- Each PT session is linked to a single trainer.

### **Member — PT_Session**
- Relationship: **1 : N**
- One member can reserve multiple PT sessions.

### **Member — Workout_Log**
- Relationship: **1 : N**
- One member can have many workout logs.

### **Exercise — Workout_Log**
- Relationship: **1 : N**
- One exercise type can appear in multiple workout logs.

### **Member — Payment**
- Relationship: **1 : N**
- A member can have multiple payment records.

---

## 📚 Relational Schema (Summary)

**Member(**  
member_id PK,  
name, phone, gender, join_date, expiry_date, remaining_pt_count  
**)**  

**Trainer(**  
trainer_id PK,  
name, specialty, career_year  
**)**  

**Exercise(**  
exercise_id PK,  
name, part  
**)**  

**PT_Session(**  
session_id PK,  
member_id FK,  
trainer_id FK,  
session_date,  
session_time,  
status  
**)**  

**Workout_Log(**  
log_id PK,  
member_id FK,  
exercise_id FK,  
log_date, weight, sets, reps, feedback  
**)**  

**Payment(**  
payment_id PK,  
member_id FK,  
amount, payment_date, method, category  
**)**  

---

## 📎 ER Diagram
<img width="1274" height="717" alt="image" src="https://github.com/user-attachments/assets/cbc83050-72ff-4657-82a0-bc232f7cf6ba" />

---

🛠 Technologies Used

Oracle SQL Developer

Oracle Database XE

SQL (DDL, DML, JOIN, Subquery)

Git / GitHub


## 🎬 Demonstration Video (Korean Version)
[![Demo Video](https://img.youtube.com/vi/XsdbgZr0mJI/0.jpg)](https://www.youtube.com/watch?v=XsdbgZr0mJI)


👤 Author

Gwangmin
Myongji University – Dept. of Computer Science

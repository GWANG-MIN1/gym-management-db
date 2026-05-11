# 🏋️‍♂️ 피트니스 센터 관리 시스템

**박광민**

![SQL Lint](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/lint.yml/badge.svg)

---

## 📌 프로젝트 개요

피트니스 센터에서 발생하는 다양한 데이터를 효율적으로 관리하기 위한 데이터베이스 시스템입니다.

회원 정보, 트레이너 배정, PT 예약 일정, 운동 기록, 결제 내역을 저장하고 관리합니다.

---

## ✔ 기능 요구사항

1. 관리자는 회원 정보를 등록, 수정, 삭제할 수 있어야 한다.
2. 회원은 특정 트레이너와 PT 세션을 예약할 수 있어야 한다.
3. 한 명의 트레이너는 여러 회원을 담당할 수 있어야 한다.
4. 회원은 운동 결과(날짜, 운동 종류, 세트, 무게 등)를 기록할 수 있어야 한다.
5. PT 예약은 날짜와 시간 단위로 관리되어야 한다.
6. 회원은 여러 건의 PT 결제를 할 수 있으며, 모든 결제 내역이 저장되어야 한다.

---

## ✔ 비기능 요구사항

1. 데이터 무결성을 유지해야 한다.
2. 정규화를 통해 데이터 중복을 최소화해야 한다.
3. 모든 엔티티는 기본 키를 포함해야 한다.
4. 삭제 및 수정 시 참조 무결성이 보장되어야 한다.

---

## 📎 ER 다이어그램

<img width="1274" height="717" alt="image" src="https://github.com/user-attachments/assets/cbc83050-72ff-4657-82a0-bc232f7cf6ba" />

---

## 🐳 로컬 실행 (Docker)

Oracle XE 환경을 Docker로 한 번에 실행할 수 있습니다.

```bash
docker compose up -d
```

- Oracle XE 21c 컨테이너가 시작되며 스키마와 샘플 데이터가 자동으로 초기화됩니다.
- 최초 실행 시 초기화에 약 2~3분 소요됩니다.

**접속 정보**

| 항목 | 값 |
|------|-----|
| Host | localhost |
| Port | 1521 |
| User | gymuser |
| Password | gymuser123 |
| SID | XE |

**컨테이너 종료**
```bash
docker compose down        # 컨테이너만 종료 (데이터 유지)
docker compose down -v     # 컨테이너 + 볼륨 삭제
```

---

## ✅ CI — SQL 린트 (GitHub Actions)

`.sql` 파일이 변경되어 push 또는 PR이 생성되면 **sqlfluff**가 자동으로 SQL 문법을 검사합니다.

```
.sql 파일 변경 push / PR
  └─ lint.yml : sqlfluff lint *.sql --dialect oracle
```

---

## 🛠 사용 기술

| 분야 | 기술 |
|------|------|
| 데이터베이스 | Oracle Database XE 21c |
| SQL | DDL, DML, JOIN, 서브쿼리, 트리거, 시퀀스 |
| 컨테이너 | Docker / Docker Compose |
| CI | GitHub Actions, sqlfluff |
| 버전 관리 | Git / GitHub |

---

## 🎬 시연 영상

[![Demo Video](https://img.youtube.com/vi/XsdbgZr0mJI/0.jpg)](https://www.youtube.com/watch?v=XsdbgZr0mJI)

---

👤 **작성자**

박광민 · 명지대학교 컴퓨터공학과

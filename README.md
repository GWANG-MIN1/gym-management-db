# Gym Management — PostgreSQL · FastAPI · AWS · Terraform

**박광민**

![SQL Lint](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/lint.yml/badge.svg)
![Schema Test](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/schema-test.yml/badge.svg)
![API Test](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/api-test.yml/badge.svg)
![Terraform CI](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/terraform.yml/badge.svg)
![CD](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/cd.yml/badge.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-≥1.6-844FBA?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-RDS·ECR·EC2·SecretsManager-FF9900?logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

피트니스 센터 운영 데이터를 관리하는 백엔드 프로젝트입니다.
로컬 Oracle XE 에서 시작해 **PostgreSQL 마이그레이션 → FastAPI 서버 → Docker 컨테이너화 →
ECR/EC2 자동 배포 → AWS Secrets Manager 보안 → CloudWatch 모니터링 → 부하 테스트**까지
단계적으로 구축했습니다.

**범위:** DB 설계와 서버 운영(배포·보안·모니터링)에 무게를 둔 프로젝트입니다.
회원용 앱이나 관리자 웹 화면은 포함돼 있지 않고, API 는 Swagger UI 로 확인합니다.

---

## 아키텍처

```
인터넷
  └─ EC2 (t3.micro, ap-northeast-2a)
       ├─ gym-api 컨테이너 (FastAPI, :8000)
       │    ├─ 시작 시 Secrets Manager 에서 DB 접속 정보 자동 로드
       │    └─ 시작 시 Alembic 마이그레이션으로 스키마를 최신으로 정렬
       └─ Private Subnet
            └─ RDS PostgreSQL 15 (Primary)
                 └─ Read Replica (선택 — create_read_replica = true 일 때만)

GitHub Actions (push 감지)
  └─ API 테스트(pytest) 통과 → Docker 이미지 빌드
       └─ ECR push
            └─ EC2 SSH 배포 → /health (DB 확인 포함) 통과 확인

CloudWatch
  ├─ RDS CPU / 커넥션 / 지연시간 대시보드
  ├─ 임계값 초과 시 이메일 알람 (SNS)
  └─ API 서버 로그 수집 (awslogs 드라이버)
```

---

## 단계별 구현 내용

| 단계 | 내용 | 기술 |
|------|------|------|
| 1 | DB 스키마 설계 (Oracle → PostgreSQL 마이그레이션) | SQL, Docker |
| 2 | FastAPI 서버 + docker-compose | FastAPI, SQLAlchemy, PostgreSQL |
| 3 | CD 파이프라인 (테스트 → 빌드 → ECR → EC2 배포) | GitHub Actions, ECR, EC2 |
| 4 | DB 비밀번호 보안 관리 | AWS Secrets Manager, IAM |
| 5 | 모니터링 + 알람 | CloudWatch, SNS |
| 6 | 부하 테스트 | k6 |
| 7 | 업무 규칙 · 예외 처리 · API 테스트 보강 | pytest |

---

## 데이터 모델

6개 테이블로 회원·트레이너·운동·PT 일정·운동 기록·결제를 관리합니다.

| 테이블 | 저장하는 내용 |
|--------|--------------|
| `Member` | 회원 정보, 가입일, 만료일, 잔여 PT 횟수 |
| `Trainer` | 트레이너 이름, 전문 분야, 경력 |
| `Exercise` | 운동 종목과 부위 |
| `PT_Session` | 회원·트레이너의 PT 일정과 상태 |
| `Workout_Log` | 운동 날짜, 중량, 세트, 반복 수, 피드백 |
| `Payment` | 결제 금액, 날짜, 수단, 구분 |

DB 레벨에서 막는 것

- 회원 전화번호 / 운동 종목명 중복
- 잔여 PT 횟수·경력·결제 금액·세트·반복 수의 음수 값
- PT 상태는 `SCHEDULED` / `COMPLETED` / `CANCELLED` 중 하나
- PT 시간은 `00:00`~`23:59` (부분 유니크 인덱스라 취소된 예약은 슬롯을 비움)
- 같은 트레이너 / 같은 회원의 같은 날짜·시간 중복 예약

**스키마 정의는 세 곳에 있고 CI 가 셋을 비교합니다.**

| 정의 | 쓰이는 곳 |
|------|----------|
| [`sql/01_create_tables_pg.sql`](sql/01_create_tables_pg.sql) | 로컬 docker compose 초기화 |
| [`api/models.py`](api/models.py) | ORM · 테스트 |
| [`api/migrations/`](api/migrations) | 배포 시 실제 적용 (Alembic) |

셋이 벌어지면 환경마다 스키마가 달라지므로, `test_schema_parity.py` 가 SQL ↔ ORM 을,
`test_migration_from_legacy.py` 가 마이그레이션 결과 ↔ ORM 을 컬럼·제약·인덱스 단위로 비교합니다.

> Oracle 용 루트 SQL 3개(`01_create_tables.sql`, `02_insert_sample_data.sql`,
> `03_project_queries.sql`)는 초기 버전의 기록입니다. 현재 서비스는 PostgreSQL 만 사용하며,
> PostgreSQL 용 샘플 데이터는 [`sql/02_insert_sample_data_pg.sql`](sql/02_insert_sample_data_pg.sql) 입니다.

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/members` | 회원 목록 (`limit`·`offset`) |
| POST | `/members` | 회원 등록 |
| GET | `/members/{id}` | 회원 상세 |
| GET | `/trainers` · `/trainers/{id}` | 트레이너 목록 / 상세 |
| POST | `/trainers` | 트레이너 등록 |
| GET | `/exercises` | 운동 종목 목록 |
| POST | `/exercises` | 운동 종목 등록 |
| GET | `/sessions` | PT 예약 목록 (회원·트레이너·상태·기간 필터) |
| GET | `/sessions/{id}` | PT 예약 상세 |
| POST | `/sessions` | PT 예약 |
| PATCH | `/sessions/{id}/complete` | PT 완료 처리 (잔여 횟수 1 차감) |
| PATCH | `/sessions/{id}/cancel` | PT 예약 취소 |
| GET | `/workouts` · `POST /workouts` | 운동 기록 조회 / 등록 |
| GET | `/payments` · `POST /payments` | 결제 기록 조회 / 등록 |
| GET | `/health` | 헬스체크 (DB `SELECT 1` 포함) |
| GET | `/health/live` | 라이브니스 (DB 미조회) |

Swagger UI: `http://<EC2_IP>:8000/docs`

**아직 없는 것:** 수정(PUT/PATCH 필드 변경)·삭제(DELETE) 엔드포인트,
역할(관리자/트레이너/회원) 기반 권한 분리, 실제 결제(카드 승인) 연동.
`Payment` 는 결제 *기록*을 저장하는 테이블입니다.

### PT 예약 업무 규칙

`POST /sessions` 는 다음을 확인합니다.

1. 회원·트레이너 존재 (없으면 404)
2. 지난 날짜 예약 불가 (422)
3. 회원권 만료일 이후 예약 불가 (409)
4. 잔여 PT 횟수 0이면 예약 불가 (409)
5. 같은 트레이너 / 같은 회원의 같은 시간대 중복 예약 불가 (409)

예약은 항상 `SCHEDULED` 로 생성되고, 상태 변경은 `/complete`·`/cancel` 로만 합니다.

**잔여 PT 횟수 차감**은 Oracle 스키마에서 트리거(`trg_pt_session_complete`)로 하던 일인데,
PostgreSQL 로 옮기면서 API 의 완료 처리로 옮겼습니다.
트리거를 함께 두면 로컬(SQL 파일로 초기화)과 배포(마이그레이션) 환경에서 차감이 두 번 일어나기 때문입니다.
차감은 상태 변경과 같은 트랜잭션에서 `remaining_pt_count > 0` 조건부 UPDATE 로 처리하며,
남은 횟수가 없으면 완료 처리 자체가 409 로 거부됩니다.

### 오류 응답

DB 제약 위반은 500 대신 이유를 담아 돌려줍니다
([`api/errors.py`](api/errors.py)).

| 상황 | 응답 |
|------|------|
| 전화번호 / 운동 종목명 중복 | 409 `이미 등록된 전화번호입니다.` |
| 같은 트레이너·시간대 중복 예약 | 409 `해당 트레이너는 같은 날짜·시간에 이미 예약이 있습니다.` |
| 없는 회원/종목 참조 (FK 위반) | 404 |
| CHECK 제약 위반 | 422 |

### 인증 (선택)

`API_KEY` 환경변수를 설정하면 쓰기(POST/PATCH) 요청에 `X-API-Key` 헤더가 필요합니다.
설정하지 않으면 인증은 비활성화됩니다. 역할 기반 권한 분리는 아직 없습니다.

---

## 로컬 실행

```bash
docker compose up -d
```

`sql/01_create_tables_pg.sql` 로 테이블을 만들고 `sql/02_insert_sample_data_pg.sql` 로
샘플 데이터(회원 10 · 트레이너 10 · 운동 10 · PT 13 · 운동기록 10 · 결제 10)까지 적재합니다.

| 항목 | 값 |
|------|----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| DB Port | 5433 (호스트) |

### 테스트

PostgreSQL 전용 제약(정규식 CHECK, 부분 유니크 인덱스)을 쓰므로 실제 PostgreSQL 에 붙여 실행합니다.

> **테스트는 테이블을 삭제·재생성합니다.** 그래서 접속 정보는 `TEST_DATABASE_URL` 로만 받고,
> DB 이름이 `_test` 로 끝나지 않으면 실행을 거부합니다. 개발용 `gymdb` 를 지우지 않기 위한 장치입니다.
> 업그레이드 테스트는 `<DB이름>_legacy` DB 를 잠시 만들었다 지우므로 계정에 DB 생성 권한이 필요합니다.

```bash
docker compose up -d db
docker compose exec -T db psql -U gymadmin -d gymdb -c "CREATE DATABASE gymdb_test"   # 최초 1회
pip install -r api/requirements-dev.txt
cd api && TEST_DATABASE_URL=postgresql://gymadmin:gymadmin123@localhost:5433/gymdb_test pytest -q
```

---

## CI/CD 파이프라인

| 워크플로우 | 하는 일 |
|-----------|--------|
| `lint.yml` | sqlfluff 로 SQL 린트 — **위반이 있으면 실패** |
| `schema-test.yml` | 스키마·샘플 데이터 적용 후 조회, 제약 위반이 실제로 거부되는지 확인 (`ON_ERROR_STOP=1`) |
| `api-test.yml` | PostgreSQL 서비스 컨테이너에 붙여 pytest 실행 |
| `terraform.yml` | `terraform fmt -check` + `validate` |
| `cd.yml` | **API 테스트 통과 후** 빌드 → ECR → EC2 배포 → `/health` 확인 |

```
api/** 코드 변경 → git push → GitHub Actions
  ├─ test (pytest + PostgreSQL)
  ├─ build-and-push
  │    ├─ Docker 이미지 빌드
  │    └─ ECR push (SHA 태그 + latest)
  └─ deploy
       ├─ EC2 SSH 접속
       ├─ docker pull → 기존 컨테이너 교체
       └─ /health (DB SELECT 1 포함) 통과 확인
```

**한계:** 기존 컨테이너를 먼저 내리고 새로 띄우므로 배포 중 짧은 중단이 생기고,
실패 시 이전 이미지로 자동 롤백하는 단계는 아직 없습니다.

---

## 스키마 마이그레이션 (Alembic)

예전에는 앱 시작 시 `create_all()` 을 호출했습니다. 하지만 `create_all()` 은 **없는 테이블만
만들 뿐 기존 테이블의 기본값·제약·인덱스는 손대지 않습니다.** 그래서 예전 스키마가 있는 DB 에
새 버전을 배포하면 `created_at` 기본값이 없어 **회원·트레이너·예약 등록이 전부 422 로 실패**했고,
예전의 일반 UNIQUE 제약이 남아 **취소한 예약의 시간대를 다시 쓸 수 없었습니다.**

지금은 컨테이너가 시작할 때 Alembic 마이그레이션을 실행합니다.

| 리비전 | 내용 |
|--------|------|
| `0001` | 예전 스키마(회원·트레이너·PT 3개 테이블) — 기존 DB 를 이력에 편입시키는 기준점 |
| `0002` | 운동·운동기록·결제 테이블 추가, 기본값 부여, 예약 중복 방지 제약을 부분 유니크 인덱스로 교체, 시각 형식 CHECK·인덱스 추가, SERIAL → IDENTITY 전환 |

```
빈 DB            → 0001 → 0002
기존 DB(이력 없음) → 0001 로 stamp → 0002 만 적용
이미 최신 DB      → 아무것도 하지 않음
```

`0002` 는 여러 번 실행해도 안전하도록 작성했습니다. 운영 DB 가 "예전 3개 테이블 +
`create_all` 이 만든 새 3개 테이블"처럼 섞인 상태여도 그대로 적용됩니다.

새 제약을 붙이기 전에 기존 데이터를 먼저 검사해, 위반하는 행이 있으면
(예: `99:99` 같은 시각, 같은 회원의 같은 시간대 중복 예약) **어떤 행이 문제인지 알려주고 중단**합니다.
이때는 컨테이너가 뜨지 않아 배포가 실패하므로, 데이터를 정리한 뒤 다시 배포해야 합니다.

`0002` 의 downgrade 는 제공하지 않습니다(테이블 추가와 IDENTITY 전환이 포함돼 자동 복구가
안전하지 않음). 되돌려야 한다면 RDS 스냅샷에서 복구합니다.

---

## 보안 — Secrets Manager

DB 비밀번호를 코드나 환경변수에 직접 노출하지 않습니다.

```
기존: DATABASE_URL(비번 포함) → GitHub Secret 평문 저장
개선: DB 비밀번호 → Secrets Manager 저장
      EC2 IAM 롤로 접근 권한 부여
      API 시작 시 자동 로드 (boto3)
```

```python
# api/database.py — 핵심 로직
secret = boto3.client("secretsmanager").get_secret_value(SecretId=secret_name)
# 코드 어디에도 비밀번호 없음
```

`.gitignore` 는 `terraform/terraform.tfvars`(DB 비밀번호 포함)를 제외합니다.
같은 줄에 주석을 붙이면 주석까지 패턴에 포함돼 무시되지 않으므로 주석은 별도 줄에 씁니다.

---

## 모니터링

CloudWatch 대시보드에서 실시간 확인:

| 지표 | 알람 조건 |
|------|----------|
| RDS CPU 사용률 | 5분 평균 80% 초과가 2회 연속이면 이메일 알람 |
| RDS 커넥션 수 | 5분 평균 20 초과가 2회 연속이면 이메일 알람 |
| RDS 읽기 지연시간 | 5분 평균 100ms 초과가 2회 연속이면 이메일 알람 |
| API 서버 로그 | CloudWatch Logs 수집 (보관 14일) |

커넥션 알람(20)에 맞춰 API 커넥션 풀은 컨테이너당 최대 15개(`pool_size=5` + `max_overflow=10`)로 둡니다.

---

## 부하 테스트 결과 (k6)

**테스트 환경:** EC2 t3.micro + RDS db.t3.micro (ap-northeast-2)
**시나리오:** VU 10명 → 30명 → 50명 단계적 증가 (총 3분 30초)

```bash
k6 run -e BASE_URL=http://<EC2_IP>:8000 load-test/k6_script.js
```

### 결과 요약 (개선 전 · 페이지네이션 없던 버전)

| 지표 | 결과 | 목표 |
|------|------|------|
| 총 요청 수 | 6,354건 | — |
| 처리량 | 30.2 req/s | — |
| 에러율 | **0%** | < 1% ✅ |
| 전체 응답시간 p(95) | 1.66s | < 500ms ❌ |
| POST /members p(95) | 365ms | < 500ms ✅ |
| GET /members p(95) | 2,046ms | < 300ms ❌ |

에러는 없었지만 **응답시간 목표(threshold)는 통과하지 못했습니다.**
k6 는 threshold 미달 시 실패로 처리하므로 "0% 에러 = 통과"가 아닙니다.

### 분석

느렸던 쪽은 읽기(`GET /members`)입니다. 당시 코드는 `db.query(Member).all()` 로
**전체 회원을 페이지네이션 없이 반환**했고, 부하 테스트가 회원을 계속 등록하는 동안
행 수가 늘면서 DB 조회뿐 아니라 ORM 객체 생성·JSON 직렬화·응답 전송량이 함께 커졌습니다.

> 처음에는 원인을 "인덱스 없음"으로 적었지만, PostgreSQL 은 PK 와 UNIQUE 제약에
> 인덱스를 자동으로 만듭니다. 전체 목록 조회는 인덱스로 해결되는 문제가 아니라
> **반환 행 수를 제한해야 하는 문제**였습니다.

### 개선 (이번 변경)

1. 모든 목록 API 에 `limit`(기본 50 · 최대 200) / `offset` 적용
2. FK·조회 조건 컬럼 인덱스 추가 (`idx_member_expiry`, `idx_pt_session_date`, …)
3. 읽기 전용 커넥션 분리 — Read Replica 가 있으면 조회를 Replica 로 보냄
4. 커넥션 풀 `pool_pre_ping` / `pool_recycle` 설정

> 위 표의 수치는 **개선 전** 기록입니다. 개선 후 수치는 같은 조건으로 다시 측정해 갱신할 예정입니다.

### Read Replica 를 켤 때

Terraform 변수만 켜면 Replica 인스턴스가 생기지만, 그것만으로 읽기 부하가 나뉘지는 않습니다.
애플리케이션이 Replica 로 가는 별도 커넥션을 써야 합니다.

```hcl
# terraform.tfvars
create_read_replica = true
```

`create_read_replica = true` 면 Terraform 이 Secrets Manager 시크릿에 `replica_host` 를 추가하고,
API 는 그 값이 있을 때만 읽기 세션(`get_read_db`)을 Replica 로 연결합니다.
로컬에서는 `READ_DATABASE_URL` 환경변수로 같은 동작을 시험할 수 있습니다.

> `multi_az`, `create_read_replica`, `storage_encrypted` 세 옵션은 **기본값이 모두 `false`** 입니다.
> 코드에 옵션이 있다는 것과 현재 켜져 있다는 것은 다릅니다.

---

## 프로젝트 구조

```
gym-management-db/
├── api/                          FastAPI 서버
│   ├── Dockerfile
│   ├── requirements.txt / requirements-dev.txt
│   ├── main.py                   앱 진입점 + 헬스체크 (시작 시 마이그레이션)
│   ├── migrate.py                Alembic 실행 (기존 DB 자동 편입)
│   ├── alembic.ini / migrations/ 스키마 마이그레이션
│   ├── database.py               DB 연결 (Secrets Manager · 읽기/쓰기 분리)
│   ├── models.py                 SQLAlchemy ORM 모델 (6개 테이블)
│   ├── schemas.py                Pydantic 요청/응답 스키마
│   ├── auth.py                   선택적 API Key 인증
│   ├── errors.py                 DB 제약 위반 → 409/404/422 변환
│   ├── pagination.py             limit / offset 공통 파라미터
│   ├── routers/                  members · trainers · exercises
│   │                             sessions · workouts · payments
│   └── tests/                    pytest (스키마 일치·업그레이드 검증 포함)
│
├── load-test/
│   └── k6_script.js              부하 테스트 스크립트
│
├── sql/
│   ├── 01_create_tables_pg.sql   PostgreSQL 15 스키마
│   └── 02_insert_sample_data_pg.sql  PostgreSQL 샘플 데이터
│
├── terraform/                    VPC · RDS · ECR · EC2 · Secrets · CloudWatch · KMS
│
├── 01_create_tables.sql          (Oracle 초기 버전 — 기록용)
├── 02_insert_sample_data.sql     (Oracle 초기 버전 — 기록용)
├── 03_project_queries.sql        (Oracle 조회 쿼리 7개 — 기록용)
│
├── docker-compose.yml            로컬 개발 (PostgreSQL + API)
└── .github/workflows/
    ├── lint.yml                  SQL 린트
    ├── schema-test.yml           PostgreSQL 스키마·제약 검증
    ├── api-test.yml              API 테스트 (pytest)
    ├── terraform.yml             Terraform fmt/validate
    └── cd.yml                    테스트 → 빌드 → ECR → EC2 배포
```

---

## AWS 배포 (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# db_password, ec2_key_name 설정

terraform init
terraform apply
```

**GitHub Secrets 설정 (CD 파이프라인):**

| Secret | 값 |
|--------|----|
| `AWS_ACCESS_KEY_ID` | IAM Access Key |
| `AWS_SECRET_ACCESS_KEY` | IAM Secret Key |
| `EC2_HOST` | `terraform output ec2_public_ip` |
| `EC2_SSH_KEY` | `.pem` 파일 전체 내용 |

---

## 기술 스택

| 분야 | 기술 |
|------|------|
| 백엔드 | FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2 |
| 데이터베이스 | PostgreSQL 15 (AWS RDS), Oracle XE 21c (초기 버전) |
| 컨테이너 | Docker, Docker Compose |
| 클라우드 | AWS EC2, RDS, ECR, Secrets Manager, CloudWatch, SNS, IAM |
| 마이그레이션 | Alembic 1.13 |
| IaC | Terraform ≥ 1.6 |
| CI/CD | GitHub Actions |
| 테스트 | pytest (API), k6 (부하) |

---

## 다음 단계

- 역할(관리자/트레이너/회원) 기반 권한 분리
- 수정·삭제 엔드포인트와 무중단 배포(롤백 포함)
- 개선 후 부하 테스트 재측정

---

👤 **박광민** · 명지대학교 컴퓨터공학과

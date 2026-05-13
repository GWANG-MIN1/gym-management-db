# Gym Management — PostgreSQL · FastAPI · AWS · Terraform

**박광민**

![SQL Lint](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/lint.yml/badge.svg)
![Schema Test](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/schema-test.yml/badge.svg)
![Terraform CI](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/terraform.yml/badge.svg)
![CD](https://github.com/GWANG-MIN1/gym-management-db/actions/workflows/cd.yml/badge.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-≥1.6-844FBA?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-RDS·ECR·EC2·SecretsManager-FF9900?logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

피트니스 센터 운영 데이터를 관리하는 풀스택 백엔드 프로젝트입니다.  
로컬 Oracle XE에서 시작해 **FastAPI 서버 → Docker 컨테이너화 → ECR/EC2 자동 배포 → AWS Secrets Manager 보안 → CloudWatch 모니터링 → 부하 테스트**까지 단계적으로 구축했습니다.

---

## 아키텍처

```
인터넷
  └─ EC2 (t3.micro, ap-northeast-2a)
       ├─ gym-api 컨테이너 (FastAPI, :8000)
       │    └─ 시작 시 Secrets Manager에서 DB 비밀번호 자동 로드
       └─ Private Subnet
            └─ RDS PostgreSQL 15 (Primary)

GitHub Actions (push 감지)
  └─ Docker 이미지 빌드
       └─ ECR push
            └─ EC2 SSH 배포 → 헬스체크 통과 확인

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
| 2 | FastAPI CRUD 서버 + docker-compose | FastAPI, SQLAlchemy, PostgreSQL |
| 3 | CD 파이프라인 (자동 빌드 → ECR → EC2 배포) | GitHub Actions, ECR, EC2 |
| 4 | DB 비밀번호 보안 관리 | AWS Secrets Manager, IAM |
| 5 | 모니터링 + 알람 | CloudWatch, SNS |
| 6 | 부하 테스트 | k6 |

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/members` | 회원 목록 |
| POST | `/members` | 회원 등록 |
| GET | `/members/{id}` | 회원 상세 |
| GET | `/trainers` | 트레이너 목록 |
| POST | `/sessions` | PT 예약 |
| GET | `/health` | 헬스체크 |

Swagger UI: `http://<EC2_IP>:8000/docs`

---

## CI/CD 파이프라인

```
api/** 코드 변경 → git push → GitHub Actions
  ├─ build-and-push
  │    ├─ Docker 이미지 빌드
  │    └─ ECR push (SHA 태그 + latest)
  └─ deploy
       ├─ EC2 SSH 접속
       ├─ docker pull → 기존 컨테이너 교체
       └─ /health 헬스체크 통과 확인
```

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

---

## 모니터링

CloudWatch 대시보드에서 실시간 확인:

| 지표 | 알람 임계값 |
|------|------------|
| RDS CPU 사용률 | 80% 초과 시 이메일 알람 |
| RDS 커넥션 수 | 20 초과 시 이메일 알람 |
| RDS 읽기 지연시간 | 100ms 초과 시 이메일 알람 |
| API 서버 로그 | CloudWatch Logs 자동 수집 |

---

## 부하 테스트 결과 (k6)

**테스트 환경:** EC2 t3.micro + RDS db.t3.micro (ap-northeast-2)  
**시나리오:** VU 10명 → 30명 → 50명 단계적 증가 (총 3분 30초)

```
k6 run load-test/k6_script.js
```

### 결과 요약

| 지표 | 결과 |
|------|------|
| 총 요청 수 | 6,354건 |
| 처리량 | 30.2 req/s |
| 에러율 | **0%** |
| 전체 응답시간 p(95) | 1.66s |
| POST /members p(95) | **365ms** ✅ |
| GET /members p(95) | **2,046ms** ⚠️ |

### 분석

```
쓰기(POST /members): p(95) = 365ms  → 빠름
읽기(GET /members):  p(95) = 2,046ms → 느림
```

**GET /members가 느린 이유:** 부하 테스트 중 회원이 계속 등록되면서 데이터가 누적되고, 인덱스 없이 전체 스캔이 발생했습니다.  
**개선 방향:** Read Replica를 활성화해 읽기 쿼리를 분산하고, 페이지네이션을 추가하면 응답시간을 대폭 줄일 수 있습니다.

```hcl
# terraform.tfvars — Read Replica 활성화
create_read_replica = true
```

---

## 프로젝트 구조

```
gym-management-db/
├── api/                          FastAPI 서버
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   앱 진입점 + 테이블 자동 생성
│   ├── database.py               DB 연결 (Secrets Manager 연동)
│   ├── models.py                 SQLAlchemy ORM 모델
│   ├── schemas.py                Pydantic 요청/응답 스키마
│   └── routers/
│       ├── members.py
│       ├── trainers.py
│       └── sessions.py
│
├── load-test/
│   └── k6_script.js              부하 테스트 스크립트
│
├── sql/
│   └── 01_create_tables_pg.sql   PostgreSQL 15 스키마
│
├── terraform/
│   ├── main.tf                   provider 설정
│   ├── variables.tf              입력 변수
│   ├── outputs.tf                엔드포인트, IP 출력
│   ├── vpc.tf                    VPC, 서브넷, 보안그룹
│   ├── rds.tf                    RDS Primary + Read Replica
│   ├── ecr.tf                    ECR 레포지토리
│   ├── ec2.tf                    EC2 + IAM 롤
│   ├── secrets.tf                Secrets Manager
│   ├── cloudwatch.tf             대시보드 + 알람
│   ├── kms.tf                    KMS 암호화 키
│   └── terraform.tfvars.example
│
├── docker-compose.yml            로컬 개발 (PostgreSQL + API)
└── .github/workflows/
    ├── lint.yml                  SQL 린트
    ├── schema-test.yml           PostgreSQL 스키마 검증
    ├── terraform.yml             Terraform fmt/validate
    └── cd.yml                    빌드 → ECR → EC2 자동 배포
```

---

## 로컬 실행

```bash
docker compose up -d
```

| 항목 | 값 |
|------|----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| DB Port | 5433 (호스트) |

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
| 데이터베이스 | PostgreSQL 15 (AWS RDS), Oracle XE 21c (로컬) |
| 컨테이너 | Docker, Docker Compose |
| 클라우드 | AWS EC2, RDS, ECR, Secrets Manager, CloudWatch, SNS, IAM |
| IaC | Terraform ≥ 1.6 |
| CI/CD | GitHub Actions |
| 테스트 | k6 (부하 테스트) |

---

👤 **박광민** · 명지대학교 컴퓨터공학과

"""DB 제약 위반을 설명 가능한 HTTP 응답으로 변환.

전화번호 중복이나 트레이너 시간대 중복은 DB 제약으로 막히지만, 예외를 잡지 않으면
psycopg2 오류가 그대로 올라가 500 이 됩니다. 여기서 제약 이름을 보고 409/404/422 로 바꿉니다.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# PostgreSQL SQLSTATE
_UNIQUE_VIOLATION = "23505"
_FOREIGN_KEY_VIOLATION = "23503"
_CHECK_VIOLATION = "23514"
_NOT_NULL_VIOLATION = "23502"

# 제약 이름 → 사용자에게 보여줄 메시지
# (이름은 sql/01_create_tables_pg.sql 과 api/models.py 에서 동일하게 지정)
_CONSTRAINT_MESSAGES = {
    "member_phone_key": "이미 등록된 전화번호입니다.",
    "exercise_name_key": "이미 등록된 운동 종목입니다.",
    "uq_trainer_slot": "해당 트레이너는 같은 날짜·시간에 이미 예약이 있습니다.",
    "uq_member_slot": "이 회원은 같은 날짜·시간에 이미 다른 예약이 있습니다.",
    "fk_pt_session_member": "회원을 찾을 수 없습니다.",
    "fk_pt_session_trainer": "트레이너를 찾을 수 없습니다.",
    "fk_workout_member": "회원을 찾을 수 없습니다.",
    "fk_workout_exercise": "운동 종목을 찾을 수 없습니다.",
    "fk_payment_member": "회원을 찾을 수 없습니다.",
    "ck_member_gender": "성별은 'M' 또는 'F' 만 가능합니다.",
    "ck_member_pt_count": "잔여 PT 횟수는 0보다 작을 수 없습니다.",
    "ck_trainer_career": "경력 연차는 0보다 작을 수 없습니다.",
    "ck_session_status": "예약 상태는 SCHEDULED / COMPLETED / CANCELLED 만 가능합니다.",
    "ck_session_time_format": "예약 시간은 00:00~23:59 형식이어야 합니다.",
    "ck_payment_amount": "결제 금액은 0보다 커야 합니다.",
    "ck_payment_method": "결제 수단은 Card / Cash / Transfer 만 가능합니다.",
    "ck_payment_category": "결제 구분은 PT / Membership / Visit 만 가능합니다.",
    "ck_workout_sets": "세트 수는 0보다 커야 합니다.",
    "ck_workout_reps": "반복 수는 0보다 커야 합니다.",
    "ck_workout_weight": "중량은 0보다 커야 합니다.",
}


def integrity_error_to_http(exc: IntegrityError) -> HTTPException:
    """IntegrityError 를 상태 코드와 한국어 메시지가 있는 HTTPException 으로 변환."""
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    constraint = getattr(getattr(orig, "diag", None), "constraint_name", None)
    message = _CONSTRAINT_MESSAGES.get(constraint)

    if pgcode == _FOREIGN_KEY_VIOLATION:
        return HTTPException(
            status.HTTP_404_NOT_FOUND, message or "참조하는 데이터를 찾을 수 없습니다."
        )
    if pgcode in (_CHECK_VIOLATION, _NOT_NULL_VIOLATION):
        return HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            message or "입력값이 데이터 제약 조건을 위반했습니다.",
        )
    # 23505(UNIQUE) 및 그 밖의 무결성 위반
    return HTTPException(status.HTTP_409_CONFLICT, message or "이미 존재하는 데이터입니다.")


def safe_commit(db: Session) -> None:
    """commit 하되, 제약 위반이면 롤백 후 설명 가능한 HTTP 오류로 바꿔 던진다."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise integrity_error_to_http(exc) from exc

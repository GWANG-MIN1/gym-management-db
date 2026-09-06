"""목록 조회 공통 페이지네이션 파라미터.

목록 API 가 전체 행을 반환하면 데이터가 쌓일수록 DB 조회·직렬화·전송량이 함께 늘어
응답이 느려집니다(부하 테스트에서 GET /members p95 가 2초까지 올라간 원인).
모든 목록 엔드포인트는 이 의존성으로 limit/offset 을 받습니다.
"""

from dataclasses import dataclass

from fastapi import Query

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
# offset 상한이 없으면 bigint 범위를 넘는 값이 DB 까지 내려가 500 이 된다.
# 범위 안이어도 offset 이 크면 그만큼 행을 건너뛰느라 느려지므로 함께 제한한다.
MAX_OFFSET = 100_000


@dataclass(frozen=True)
class Pagination:
    limit: int
    offset: int


def pagination(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="한 번에 가져올 최대 건수"),
    offset: int = Query(0, ge=0, le=MAX_OFFSET, description="건너뛸 건수"),
) -> Pagination:
    return Pagination(limit=limit, offset=offset)

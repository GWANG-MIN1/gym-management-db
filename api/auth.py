"""선택적 API Key 인증.

API_KEY 환경변수가 설정돼 있을 때만 동작하며, 데이터를 바꾸는 엔드포인트(POST/PATCH)에
`X-API-Key` 헤더를 요구합니다. 값을 설정하지 않으면 인증은 비활성화되므로
로컬 개발과 기존 배포는 그대로 동작합니다.

  docker run -e API_KEY=... 또는 docker compose 의 environment 로 주입

아직 관리자/트레이너/회원 역할별 권한 분리는 없습니다. 역할 기반 접근 제어가 필요하면
사용자 테이블과 토큰 발급(JWT 등)을 추가해야 합니다.
"""

import hmac
import os

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected = os.getenv("API_KEY")
    if not expected:
        return  # 키 미설정 = 인증 비활성화

    if x_api_key is None or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 X-API-Key 헤더가 필요합니다.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

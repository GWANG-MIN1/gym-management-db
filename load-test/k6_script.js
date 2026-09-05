import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

// ── 커스텀 메트릭 ──────────────────────────────────────────────
const listMembersDuration = new Trend("list_members_duration");
const createMemberDuration = new Trend("create_member_duration");
const errorRate = new Rate("error_rate");

// ── 테스트 시나리오 ────────────────────────────────────────────
// 단계별로 부하를 올렸다가 내림 (ramp-up → peak → ramp-down)
export const options = {
  stages: [
    { duration: "30s", target: 10 },  // 30초 동안 10명까지 증가
    { duration: "1m",  target: 30 },  // 1분 동안 30명 유지
    { duration: "30s", target: 50 },  // 30초 동안 50명까지 증가
    { duration: "1m",  target: 50 },  // 1분 동안 50명 유지 (peak)
    { duration: "30s", target: 0  },  // 30초 동안 0명으로 감소
  ],
  thresholds: {
    http_req_duration:       ["p(95)<500"],  // 95% 요청이 500ms 이하
    http_req_failed:         ["rate<0.01"],  // 에러율 1% 미만
    list_members_duration:   ["p(95)<300"],
    create_member_duration:  ["p(95)<500"],
  },
};

// 대상 서버는 환경변수로 지정한다 (IP 를 코드에 박아두지 않음)
//   k6 run -e BASE_URL=http://<EC2_IP>:8000 load-test/k6_script.js
//   API_KEY 를 설정한 서버라면 -e API_KEY=... 도 함께 전달
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const PAGE_SIZE = __ENV.PAGE_SIZE || 50;

const writeHeaders = { "Content-Type": "application/json" };
if (__ENV.API_KEY) {
  writeHeaders["X-API-Key"] = __ENV.API_KEY;
}

function isoDate(offsetDays) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

export default function () {
  // 1. 회원 목록 조회 (읽기 — Replica 가 있으면 Replica, 없으면 Primary)
  //    페이지네이션이 생겨 전체 행을 직렬화하지 않는다
  const listRes = http.get(`${BASE_URL}/members?limit=${PAGE_SIZE}`, {
    tags: { name: "GET /members" },
  });
  listMembersDuration.add(listRes.timings.duration);
  errorRate.add(listRes.status !== 200);
  check(listRes, { "GET /members 200": (r) => r.status === 200 });

  sleep(0.5);

  // 2. 트레이너 목록 조회
  const trainerRes = http.get(`${BASE_URL}/trainers?limit=${PAGE_SIZE}`, {
    tags: { name: "GET /trainers" },
  });
  errorRate.add(trainerRes.status !== 200);
  check(trainerRes, { "GET /trainers 200": (r) => r.status === 200 });

  sleep(0.5);

  // 3. 회원 등록 (쓰기 — Primary DB INSERT)
  const phone = `010-${Math.floor(1000 + Math.random() * 9000)}-${Math.floor(1000 + Math.random() * 9000)}`;
  const createRes = http.post(
    `${BASE_URL}/members`,
    JSON.stringify({
      name: "부하테스트",
      phone: phone,
      gender: "M",
      join_date: isoDate(0),
      expiry_date: isoDate(365),
      remaining_pt_count: 5,
    }),
    { headers: writeHeaders, tags: { name: "POST /members" } }
  );
  createMemberDuration.add(createRes.timings.duration);
  errorRate.add(createRes.status !== 201);
  check(createRes, { "POST /members 201": (r) => r.status === 201 });

  sleep(1);
}

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

const BASE_URL = "http://43.203.233.160:8000";

export default function () {
  // 1. 회원 목록 조회 (읽기 — Primary DB 쿼리)
  const listRes = http.get(`${BASE_URL}/members`);
  listMembersDuration.add(listRes.timings.duration);
  errorRate.add(listRes.status !== 200);
  check(listRes, { "GET /members 200": (r) => r.status === 200 });

  sleep(0.5);

  // 2. 트레이너 목록 조회
  const trainerRes = http.get(`${BASE_URL}/trainers`);
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
      join_date: "2026-05-13",
      expiry_date: "2027-05-13",
      remaining_pt_count: 5,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
  createMemberDuration.add(createRes.timings.duration);
  errorRate.add(createRes.status !== 201);
  check(createRes, { "POST /members 201": (r) => r.status === 201 });

  sleep(1);
}

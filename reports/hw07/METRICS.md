# HW7 Metrics

## Part 1 — JWT Auth & RBAC

| Scenario | Expected | Actual | Pass? |
|----------|----------|--------|-------|
| POST /auth/login valid creds | 200 + token | | |
| POST /auth/login wrong password | 401 | | |
| GET /auth/me with valid token | 200 + role | | |
| GET /api/vulnerabilities no token | 401 | | |
| GET /api/vulnerabilities reader token | 200 | | |
| POST /api/vulnerabilities reader token | 403 | | |
| POST /api/vulnerabilities writer token | 201 | | |
| DELETE /api/vulnerabilities writer token | 403 | | |
| DELETE /api/vulnerabilities moderator token | 200 | | |

## Part 2 — Tool-call Reliability

| Metric | Value |
|--------|-------|
| Pass rate | /20 |
| Avg latency (s) | |

## Part 3 — Reflexion

| Metric | Base | Reflexion |
|--------|------|-----------|
| Answer quality | | |
| Iterations | 0 | |


import time
import requests
import numpy as np

BASE_URL = "http://localhost:8044/api/vulnerabilities"

# Test endpoint at page sizes 10, 50, 200
page_sizes = [10, 50, 200]
session = requests.Session()

# Log in once
login_response = session.post(
    "http://localhost:8044/auth/login",
    json={
        "email": "admin@example.com",
        "password": "password"
    }
)
# Make sure login worked
if login_response.status_code != 200:
    print("Login failed")
    exit()

print("Successfully logged in")

for page_size in page_sizes:
    latencies = []  #p50, p95, p99 latency
    query_counts = []   # how many queries each request triggers

    # Run 30 requests for each size
    for i in range(30):
        start = time.perf_counter()
        response = session.get(BASE_URL, params={"page_size": page_size})

        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

        query_counts.append(int(response.headers["X-Query-Count"]))

    print(f"\nPage size: {page_size}")
    print(f"Queries/request: {query_counts[0]}")
    print(f"p50: {np.percentile(latencies, 50):.2f} ms")
    print(f"p95: {np.percentile(latencies, 95):.2f} ms")
    print(f"p99: {np.percentile(latencies, 99):.2f} ms")
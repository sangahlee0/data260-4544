import time
import requests
import numpy as np
import csv
import os

#BASE_URL = "http://localhost:8044/api/vulnerabilities"

# Test endpoint at page sizes 10, 50, 200
page_sizes = [10, 50, 200]
session = requests.Session()
data_file = []   # used for csv

# Test both versions of naive and fixed
versions = {
    "naive": "/api/vulnerabilities",
    "fixed": "/api/vulnerabilities-fixed"
}

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

# Test and give results for naive and fixed
for ver, link in versions.items():
    for page_size in page_sizes:
        latencies = []  #p50, p95, p99 latency
        query_counts = []   # how many queries each request triggers

        # Run 30 requests for each size
        for i in range(30):
            start = time.perf_counter()
            response = session.get(f"http://localhost:8044{link}", params={"page_size": page_size})

            end = time.perf_counter()

            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
            query_count = int(response.headers["X-Query-Count"])
            query_counts.append(query_count)

            data_file.append({"run": i + 1, "version": ver, "page_size": page_size, "query_count": query_count, "latency_ms": latency_ms})
            
        print(f"\nVersion: {ver}")
        print(f"\nPage size: {page_size}")
        print(f"Queries/request: {query_counts[0]}")
        print(f"p50: {np.percentile(latencies, 50):.2f} ms")
        print(f"p95: {np.percentile(latencies, 95):.2f} ms")
        print(f"p99: {np.percentile(latencies, 99):.2f} ms")


## Move to CSV
raw_folder = "../reports/hw04/raw"
os.makedirs(raw_folder, exist_ok=True)

with open(f"{raw_folder}/benchmark_raw.csv", "w",newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["run", "version", "page_size", "query_count", "latency_ms"]
    )

    writer.writeheader()
    writer.writerows(data_file)

print("\nThe data saved in a csv found in '../reports/hw04/raw.'")
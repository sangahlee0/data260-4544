import os
import sys

# python -m mongo.main --4  or --12 or --30 for the short-term memory comparison
if __name__ == "__main__":
    for n in ("4", "12", "30"):
        if "--" + n in sys.argv:
            os.environ["SHORT_TERM_N"] = n
            break
    if "--evict" in sys.argv:   # for Part 3, eviction comparison
        os.environ["EVICT"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.vulnerabilities import router as vulnerabilities_router
from routers.memory import router as memory_router

app = FastAPI(title="Vulnerability API (FastAPI + PyMongo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vulnerabilities_router)
app.include_router(memory_router)

@app.get("/")
def health():
    return {"status": "ok", "message": "Study Planner API is running"}


if __name__ == "__main__":
    print("SHORT_TERM_N =", os.environ.get("SHORT_TERM_N", "12"))

    # Reads memory_probes.yaml
    if "--probes" in sys.argv:
        index = sys.argv.index("--probes")
        session_id = sys.argv[index + 1]
        import routers.memory as memory
        memory.run_probes("sangah", session_id)
    else:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8044)
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from pathlib import Path
#from routers.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from routers.api_auth import router as api_auth_router
from sqlalchemy.orm import Session


from backend.database import Base, engine, get_db
from backend import crud, schema, models
from backend.session_crud import create_session, get_session, delete_session

# Creates the tables from models.py
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="User Management API", version="1.0.0")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check the session
def require_session(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_id")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")
    s = get_session(db, token)
    if not s:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return s  # contains user_id

@app.get("/health")
def health():
    return {"status": "ok"}


# CRUD
# REST API Endpoints

from fastapi import Response

# Create 
@app.get("/api/vulnerabilities", response_model=schema.VulnerabilityOut)
# Search can be a string or None; if omitted, it defaults to None
def get_vulnerabilities(response: Response, search: str | None = None, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Get all vulnerabilities - Returns JSON array of vulnerability objects"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache" # making sure we don't use a cached version of this response
    response.headers["Expires"] = "0"

    vulnerabilities = crud.get_vulnerabilities(db)

    if search:
        # Filter vulnerabilities based on search query (case-insensitive)
        search = search.lower()
        # Return vulnerabilities where the search term is in package_name or vulnerability_name
        return [v for v in vulnerabilities if search in v.package_name.lower() or search in v.vulnerability_name.lower()]
    return vulnerabilities

@app.post("/api/vulnerabilities", response_model=schema.VulnerabilityCreate, status_code=201)
def create_vulnerability(vulnerability_data: schema.VulnerabilityCreate, db: Session = Depends(get_db), _session=Depends(require_session)):
    if not vulnerability_data.package_name.strip():
        raise HTTPException(status_code=400, detail="Package name is required")
    
    # Generate new id
    return crud.create_vulnerability(db, vulnerability_data)

# GET vulnerability using the ID
@app.put("/api/vulnerabilities/{vulnerability_id}", response_model=schema.VulnerabilityOut)
def update_record(vulnerability_id: int, payload: schema.VulnerabilityUpdate, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Update an existing vulnerability - Accepts JSON with vulnerability details"""
    vulnerability = crud.get_vulnerability(db, vulnerability_id)
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    if not payload.package_name.strip():
        raise HTTPException(status_code=400, detail="Package name is required")

    return vulnerability

# DELETE
@app.delete("/api/vulnerabilities/{vulnerability_id}", response_model=schema.VulnerabilityOut)
def delete_vulnerability(vulnerability_id: int, db: Session = Depends(get_db)):
    """Delete a vulnerability by ID"""
    vulnerability = crud.delete_vulnerability(db, vulnerability_id)
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    return vulnerability

# Add the vulnerabilities page
@app.get("/vulnerabilities")
async def vulnerabilities_page():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/api/vulnerabilities/{vulnerability_id}", response_model=Vulnerability)
async def get_vulnerability_by_id(vulnerability_id: int):
    vulnerability = next(
        (v for v in vulnerabilities if v.id == vulnerability_id),
        None
    )
    if not vulnerability:
        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    return vulnerability

from starlette.middleware.sessions import SessionMiddleware
import os

# Secret key for session signing
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

# Enable session support
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    httponly=True,
    same_site="lax",
    max_age=3600
)

# Register routes
app.include_router(api_auth_router)


# Mount static files directory for serving HTML/CSS/JS; changed from / so that it doens't rewrite others
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

import webbrowser

# Start the server
if __name__ == "__main__":
    # Open the browser automatically
    #webbrowser.open("http://localhost:8044")
    uvicorn.run(app, host="0.0.0.0", port=8044)

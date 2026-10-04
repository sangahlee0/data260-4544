from fastapi import FastAPI, HTTPException, Depends, Request, Response
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
from backend.session_crud import get_session

# Creates the tables from models.py
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent

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

# Get all vulnerabilities 
@app.get("/api/vulnerabilities")
def get_vulnerabilities(response: Response, search: str | None = None, page_size: int = 10, db: Session = Depends(get_db), _session=Depends(require_session)):
    global sql_query_count
    sql_query_count = 0

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # Get vulnerabilities
    vulnerabilities = crud.get_vulnerabilities(db)

    if search:
        search = search.lower()
        vulnerabilities = [ v for v in vulnerabilities if search in v.vulnerability_name.lower() or search in crud.get_package(db, v.package_id).name.lower()]

    # Limit results based on page size (10, 50, 200)
    vulnerabilities = vulnerabilities[:page_size]

    results = []
    # Get the related description for each vulnerability
    for vulnerability in vulnerabilities:
        # Merge tables
        descriptions = db.query(models.VulnerabilityDescription).filter(models.VulnerabilityDescription.vulnerability_id == vulnerability.id).all()

        results.append({
            "id": vulnerability.id,
            "package_id": vulnerability.package_id,
            "package_name": crud.get_package(db, vulnerability.package_id).name,
            "vulnerability_name": vulnerability.vulnerability_name,
            "vulnerability_code": vulnerability.vulnerability_code,
            "urgency_score": vulnerability.urgency_score,
            "descriptions": [{"id": description.id, "description": description.description} for description in descriptions]
            })
    response.headers["X-Query-Count"] = str(sql_query_count)
    return results


# Fix n+1 issue for part 5 of the question
@app.get("/api/vulnerabilities-fixed")
def get_vulnerabilities_fixed(response: Response, page_size: int = 10, db: Session = Depends(get_db), _session=Depends(require_session)):
    global sql_query_count
    sql_query_count = 0

    # Get vulnerabilities and their descriptions using a JOIN
    # First get exactly the requested number of vulnerability IDs
    vulnerability_ids = [row.id
        for row in (db.query(models.Vulnerability.id).order_by(models.Vulnerability.id.asc())
            .limit(page_size).all()
        )
    ]

    # JOIN vulnerabilities with their descriptions
    rows = (
        db.query(
            models.Vulnerability,
            models.Package,
            models.VulnerabilityDescription
        )
        .join(
            models.Package,
            models.Vulnerability.package_id == models.Package.id
        )
        .outerjoin(
            models.VulnerabilityDescription,
            models.Vulnerability.id
            == models.VulnerabilityDescription.vulnerability_id
        )
        .filter(
            models.Vulnerability.id.in_(vulnerability_ids)
        )
        .order_by(models.Vulnerability.id.asc())
        .all()
    )

    results = {}

    for vulnerability, package, description in rows:
        # Add vulnerability once
        if vulnerability.id not in results:
            results[vulnerability.id] = {
                "id": vulnerability.id,
                "package_id": vulnerability.package_id,
                "package_name": package.name,
                "vulnerability_name": vulnerability.vulnerability_name,
                "vulnerability_code": vulnerability.vulnerability_code,
                "urgency_score": vulnerability.urgency_score,
                "descriptions": []
            }

        # Add description if one exists
        if description:
            results[vulnerability.id]["descriptions"].append({
                "id": description.id,
                "description": description.description
            })

    response.headers["X-Query-Count"] = str(sql_query_count)

    return list(results.values())



'''@app.get("/api/vulnerabilities", response_model=list[schema.VulnerabilityOut])
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
    return vulnerabilities'''

@app.post("/api/vulnerabilities", response_model=schema.VulnerabilityOut, status_code=201)
def create_vulnerability(vulnerability_data: schema.VulnerabilityCreate, db: Session = Depends(get_db), _session=Depends(require_session)):
    package = crud.get_package(db, vulnerability_data.package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Invalid package_id: Package does not exist")

    # Check if vulnerability_code is unique
    existing_vulnerability = db.query(models.Vulnerability).filter(models.Vulnerability.vulnerability_code == vulnerability_data.vulnerability_code).first()
    if existing_vulnerability:
        raise HTTPException(status_code=409, detail="Vulnerability with this vulnerability_code already exists")
    # Create vulnerability in MySQL
    return crud.create_vulnerability(db, vulnerability_data)

# Update vulnerability using the ID
@app.put("/api/vulnerabilities/{vulnerability_id}", response_model=schema.VulnerabilityOut)
def update_record(vulnerability_id: int, payload: schema.VulnerabilityUpdate, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Update an existing vulnerability - Accepts JSON with vulnerability details"""
    # Check if the package exists before updating the vulnerability
    package = crud.get_package(db, payload.package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Invalid package_id: Package does not exist")

    existing_vulnerability = db.query(models.Vulnerability).filter(models.Vulnerability.vulnerability_code == payload.vulnerability_code, models.Vulnerability.id != vulnerability_id).first()
    if existing_vulnerability:
        raise HTTPException(status_code=409, detail="Vulnerability with this vulnerability_code already exists")
    
    vulnerability = crud.update_vulnerability(db, vulnerability_id, payload)
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    return vulnerability

# DELETE
@app.delete("/api/vulnerabilities/{vulnerability_id}", response_model=schema.VulnerabilityOut)
def delete_vulnerability(vulnerability_id: int, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Delete a vulnerability by ID"""
    vulnerability = crud.delete_vulnerability(db, vulnerability_id)
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    return vulnerability

# Add the vulnerabilities page
@app.get("/vulnerabilities")
async def vulnerabilities_page():
    return FileResponse(BASE_DIR / "index.html")

# get by ID
@app.get("/api/vulnerabilities/{vulnerability_id}", response_model=schema.VulnerabilityOut)
def get_vulnerability_by_id(vulnerability_id: int, db:Session = Depends(get_db), _session=Depends(require_session)):
    vulnerability = crud.get_vulnerability(db, vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    return vulnerability


from sqlalchemy import event

sql_query_count = 0

@event.listens_for(engine, "before_cursor_execute")
def track_query_counts(conn, cursor, statement, parameters, context, executemany):
    global sql_query_count
    sql_query_count += 1

# from starlette.middleware.sessions import SessionMiddleware
# import os

# # Secret key for session signing
# SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

# # Enable session support
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=SECRET_KEY,
#     httponly=True,
#     same_site="lax",
#     max_age=3600
# )


# Packages api
@app.get("/api/packages", response_model=list[schema.PackageOut])
def get_packages(skip: int = 0, limit: int = 15, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Get all packages - Returns JSON array of package objects"""
    return crud.get_packages(db, skip, limit)

@app.post("/api/packages", response_model=schema.PackageOut, status_code=201)
def create_package(package_data: schema.PackageCreate, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Create a new package - Accepts JSON with package details"""
    # Check if the package already exists
    existing_package = db.query(models.Package).filter(models.Package.package_code == package_data.package_code).first()
    if existing_package:
        raise HTTPException(status_code=409, detail="Package with this package_code already exists")
    return crud.create_package(db, package_data)

@app.get("/api/packages/{package_id}", response_model=schema.PackageOut)
def get_package_by_id(package_id: int, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Get a package by ID - Returns JSON object of the package"""
    package = crud.get_package(db, package_id)
    if not package:
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )
    return package

@app.put("/api/packages/{package_id}", response_model=schema.PackageOut)
def update_package(package_id: int, payload: schema.PackageUpdate, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Update an existing package - Accepts JSON with package details"""
    # Check if a package uses the package_code
    existing_package = db.query(models.Package).filter(models.Package.package_code == payload.package_code, models.Package.id != package_id).first()
    if existing_package:
        raise HTTPException(status_code=409, detail="Package with this package_code already exists")

    package = crud.update_package(db, package_id, payload)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

@app.delete("/api/packages/{package_id}", response_model=schema.PackageOut)
def delete_package(package_id: int, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Delete a package by ID"""
    package = crud.delete_package(db, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    if package is False:
        raise HTTPException(status_code=409, detail="Package cannot be deleted because it has associated vulnerabilities")
    return package


# Relationship endpoint
@app.get("/api/packages/{package_id}/vulnerabilities", response_model=list[schema.VulnerabilityOut])
def get_vulnerabilities_by_package(package_id: int, db: Session = Depends(get_db), _session=Depends(require_session)):
    """Get all vulnerabilities for a specific package - Returns JSON array of vulnerability objects"""
    package = crud.get_package(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    vulnerabilities = crud.get_vulnerabilities_by_package(db, package_id)
    return vulnerabilities

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

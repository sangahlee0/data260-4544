from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="User Management API", version="1.0.0")

# Pydantic models for request/response validation
class Vulnerability(BaseModel):
    id: int
    package_name: str
    vulnerability_name: str
    reporter_email: str
    severity: str
    issue_description: str

class VulnerabilityCreate(BaseModel):
    package_name: str
    vulnerability_name: str
    reporter_email: str
    severity: str
    issue_description: str

class VulnerabilityUpdate(BaseModel):
    package_name: str
    vulnerability_name: str
    reporter_email: str
    severity: str
    issue_description: str
"""
# In-memory vulnerability storage
vulnerabilities: List[Vulnerability] = [
    Vulnerability(id=1, package_name="express", vulnerability_name="SQL Injection", reporter_email="alice@example.com", severity="high", issue_description="SQL injection vulnerability found in express package"),
    Vulnerability(id=2, package_name="react", vulnerability_name="Cross-Site Scripting", reporter_email="bob@example.com", severity="medium", issue_description="XSS vulnerability found in react package")
]
"""
# Empty list to store vulnerabilities
vulnerabilities: List[Vulnerability] = []

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse(BASE_DIR / "index.html")

# REST API Endpoints

from fastapi import Response

@app.get("/api/vulnerabilities", response_model=List[Vulnerability])
# Search can be a string or None; if omitted, it defaults to None
async def get_vulnerabilities(response: Response, search: str | None = None):
    """Get all vulnerabilities - Returns JSON array of vulnerability objects"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache" # making sure we don't use a chaced version of this response
    response.headers["Expires"] = "0"

    if search:
        # Filter vulnerabilities based on search query (case-insensitive)
        search = search.lower()
        # Return vulnerabilities where the search term is in package_name or vulnerability_name
        return [v for v in vulnerabilities if search in v.package_name.lower() or search in v.vulnerability_name.lower()]
    return vulnerabilities

@app.post("/api/vulnerabilities", response_model=Vulnerability, status_code=201)
async def create_vulnerability(vulnerability_data: VulnerabilityCreate):
    """Create a new vulnerability - Accepts JSON with vulnerability details"""
    if not vulnerability_data.package_name.strip():
        raise HTTPException(status_code=400, detail="Package name is required")
    
    # Generate new ID
    new_id = max([v.id for v in vulnerabilities], default=0) + 1
    new_vulnerability = Vulnerability(id=new_id, package_name=vulnerability_data.package_name, vulnerability_name=vulnerability_data.vulnerability_name, reporter_email=vulnerability_data.reporter_email, severity=vulnerability_data.severity, issue_description=vulnerability_data.issue_description)
    vulnerabilities.append(new_vulnerability)
    
    print(f"Created vulnerability: {new_vulnerability}")
    return new_vulnerability

@app.put("/api/vulnerabilities/{vulnerability_id}", response_model=Vulnerability)
async def update_record(vulnerability_id: int, vulnerability_data: VulnerabilityUpdate):
    """Update an existing vulnerability - Accepts JSON with vulnerability details"""
    vulnerability = next((v for v in vulnerabilities if v.id == vulnerability_id), None)
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    if not vulnerability_data.package_name.strip():
        raise HTTPException(status_code=400, detail="Package name is required")

    vulnerability.package_name = vulnerability_data.package_name
    vulnerability.vulnerability_name = vulnerability_data.vulnerability_name
    vulnerability.reporter_email = vulnerability_data.reporter_email
    vulnerability.severity = vulnerability_data.severity
    vulnerability.issue_description = vulnerability_data.issue_description
    print(f"Updated vulnerability: {vulnerability}")
    return vulnerability

@app.delete("/api/vulnerabilities/{vulnerability_id}", status_code=204)
async def delete_vulnerability(vulnerability_id: int):
    """Delete a vulnerability by ID"""
    global vulnerabilities
    vulnerability_index = next((index for index, vulnerability in enumerate(vulnerabilities) if vulnerability.id == vulnerability_id), None)
    
    if vulnerability_index is None:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    deleted_vulnerability = vulnerabilities.pop(vulnerability_index)
    print(f"Deleted vulnerability: {deleted_vulnerability}")
    return None

# Mount static files directory for serving HTML/CSS/JS
app.mount("/", StaticFiles(directory=BASE_DIR), name="static")

import webbrowser

# Start the server
if __name__ == "__main__":
    # Open the browser automatically
    webbrowser.open("http://localhost:8044")
    uvicorn.run(app, host="0.0.0.0", port=8044)

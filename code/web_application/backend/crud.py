from sqlalchemy.orm import Session
from . import models, schema
from datetime import datetime, timedelta, timezone


def create_vulnerability(db: Session, payload: schema.VulnerabilityCreate):
    vulnerability = models.Vulnerability(package_id=payload.package_id, vulnerability_name=payload.vulnerability_name, vulnerability_code=payload.vulnerability_code, count=payload.count)
    db.add(vulnerability)
    db.commit()
    db.refresh(vulnerability)
    return vulnerability

def get_vulnerabilities(db: Session, skip: int = 0, limit: int = 15):
    return db.query(models.Vulnerability).order_by(models.Vulnerability.id.asc()).offset(skip).limit(limit).all()

def get_vulnerability(db: Session, vulnerability_id: int):
    return db.query(models.Vulnerability).filter(models.Vulnerability.id == vulnerability_id).first()

def update_vulnerability(db: Session, vulnerability_id: int, payload: schema.VulnerabilityUpdate):
    vulnerability = get_vulnerability(db, vulnerability_id)
    if not vulnerability:
        return None
    vulnerability.package_id = payload.package_id
    vulnerability.vulnerability_name = payload.vulnerability_name
    vulnerability.vulnerability_code = payload.vulnerability_code
    vulnerability.count = payload.count
    db.commit()
    db.refresh(vulnerability)
    return vulnerability

def delete_vulnerability(db: Session, vulnerability_id: int):
    vulnerability = get_vulnerability(db, vulnerability_id)
    if not vulnerability:
        return None
    db.delete(vulnerability)
    db.commit()
    return vulnerability


# Helper for getting email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(
        models.User.email == email
    ).first()

# Helper for getting user by id
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(
        models.User.id == user_id).first()


################# Update CRUD endpoints for both the entities
def create_package(db: Session, payload: schema.PackageCreate):
    package = models.Package(name=payload.name, version=payload.version, package_code=payload.package_code)
    db.add(package)
    db.commit()
    db.refresh(package)
    return package

def get_packages(db: Session, skip: int = 0, limit: int = 15):
    return db.query(models.Package).order_by(models.Package.id.asc()).offset(skip).limit(limit).all()

def get_package(db: Session, package_id: int):
    return db.query(models.Package).filter(models.Package.id == package_id).first()

def update_package(db: Session, package_id: int, payload: schema.PackageUpdate):
    package = get_package(db, package_id)
    if not package:
        return None
    package.name = payload.name
    package.version = payload.version
    package.package_code = payload.package_code
    db.commit()
    db.refresh(package)
    return package

def delete_package(db: Session, package_id: int):
    package = get_package(db, package_id)
    if not package:
        return None
    vulnerabilities = get_vulnerabilities_by_package(db, package_id)
    # Prevent deletion if there are associated vulnerabilities
    if vulnerabilities:
        return False
    db.delete(package)
    db.commit()
    return package

# Get all primary-entity records associated with a specific secondary-entity record
def get_vulnerabilities_by_package(db: Session, package_id: int):
    return db.query(models.Vulnerability).filter(models.Vulnerability.package_id == package_id).all()

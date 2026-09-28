from sqlalchemy.orm import Session
from . import models, schema
from datetime import datetime, timedelta, timezone


def create_vulnerability(db: Session, payload: schema.VulnerabilityCreate):
    vulnerability = models.Vulnerability(package_name=payload.package_name, vulnerability_name=payload.vulnerability_name)
    db.add(vulnerability)
    db.commit()
    db.refresh(vulnerability)
    return vulnerability

def get_vulnerabilities(db: Session):
    return db.query(models.Vulnerability).order_by(models.Vulnerability.id.asc()).all()

def get_vulnerability(db: Session, vulnerability_id: int):
    return db.query(models.Vulnerability).filter(models.Vulnerability.id == vulnerability_id).first()

def update_vulnerability(db: Session, vulnerability_id: int, payload: schema.VulnerabilityUpdate):
    vulnerability = get_vulnerability(db, vulnerability_id)
    if not vulnerability:
        return None
    vulnerability.package_name = payload.package_name
    vulnerability.vulnerability_name = payload.vulnerability_name
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


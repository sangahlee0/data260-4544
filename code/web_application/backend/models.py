from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from .database import Base
from sqlalchemy.sql import func

# Domain Entity
class Vulnerability(Base):
    __tablename__= "vulnerabilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    package_name = Column(String(255), nullable=False)
    vulnerability_name = Column(String(255), nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)


class SessionToken(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)  # session token
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)


# Create table related table for testing
class VulnerabilityDescription(Base):
    __tablename__ = "vulnerability_description"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
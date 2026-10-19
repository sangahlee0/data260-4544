from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class VulnerabilityCreate(BaseModel):
    vulnerability_name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    status: Literal["open", "investigating", "resolved"] = "open"
    severity: Literal["low", "medium", "high", "critical"]
    discovered_at: datetime


class VulnerabilityUpdate(BaseModel):
    vulnerability_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    description: Optional[str] = None
    status: Optional[Literal["open", "investigating", "resolved"]] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    discovered_at: Optional[datetime] = None


class VulnerabilityOut(BaseModel):
    id: str
    vulnerability_name: str
    description: Optional[str] = None
    status: str
    severity: str
    discovered_at: datetime
    created_at: datetime
    updated_at: datetime


### PART 2
class MessageCreate(BaseModel):
    user_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str


class MessageOut(BaseModel):
    id: str
    user_id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class SummaryCreate(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    scope: Literal["session", "user"]
    text: str


class SummaryOut(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    scope: Literal["session", "user"]
    text: str
    created_at: datetime


class EpisodeCreate(BaseModel):
    user_id: str
    session_id: str
    fact: str
    importance: float = Field(ge=0, le=1)
    embedding: list[float]


class EpisodeOut(BaseModel):
    id: str
    user_id: str
    session_id: str
    fact: str
    importance: float
    embedding: list[float]
    created_at: datetime


# Memory
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str = Field(min_length=1)


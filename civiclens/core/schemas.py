"""Input checks and the read-only shapes that services return to the UI."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["Roads", "Drainage", "Waste management", "Water supply", "Streetlights", "Public safety", "Other"]
Urgency = Literal["High", "Medium", "Low"]


class RegisterIn(BaseModel):
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")  # runs before the pattern check, so stray spaces are fine
    @classmethod
    def clean_email(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ComplaintCreate(BaseModel):
    description: str = Field(min_length=5, max_length=2000)
    area: Optional[str] = Field(default=None, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("description", "area", mode="before")  # strip first so length limits count real characters
    @classmethod
    def strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class AssignIn(BaseModel):
    category: Category
    urgency: Urgency
    department_id: Optional[int] = None  # empty means the default team for the category
    note: Optional[str] = Field(default=None, max_length=500)


class StatusIn(BaseModel):
    status: Literal["In Progress", "Resolved"]
    note: Optional[str] = Field(default=None, max_length=500)


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    note: str
    created_at: datetime


class ComplaintOut(BaseModel):
    ref: str
    description: str
    area: Optional[str]
    latitude: float
    longitude: float
    status: str
    suggested_category: Optional[str]
    suggested_urgency: Optional[str]
    category: Optional[str]
    urgency: Optional[str]
    department: Optional[str]
    reporter_name: Optional[str]
    ai_summary: Optional[str] = None
    ai_source: Optional[str] = None  # "ai" or "rules"
    ai_note: Optional[str] = None
    created_at: datetime
    events: list[EventOut] = []

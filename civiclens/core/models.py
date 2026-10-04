from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="citizen")  # "citizen" or "officer"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    ref: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(Text)
    area: Mapped[Optional[str]] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="Submitted", index=True)

    # What the system suggested. Never overwritten, so accuracy can be measured later.
    suggested_category: Mapped[Optional[str]] = mapped_column(String(40))
    suggested_urgency: Mapped[Optional[str]] = mapped_column(String(10))

    # What the officer confirmed. This is the record.
    category: Mapped[Optional[str]] = mapped_column(String(40))
    urgency: Mapped[Optional[str]] = mapped_column(String(10))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    reporter: Mapped[User] = relationship()
    department: Mapped[Optional[Department]] = relationship()
    events: Mapped[list["StatusEvent"]] = relationship(
        back_populates="complaint", order_by="StatusEvent.id", cascade="all, delete-orphan"
    )
    analysis: Mapped[Optional["AIAnalysis"]] = relationship(cascade="all, delete-orphan")


class StatusEvent(Base):
    """One row per change: the timeline the citizen sees and the audit trail officers rely on."""

    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default="")
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    complaint: Mapped[Complaint] = relationship(back_populates="events")


class AIAnalysis(Base):
    """How the suggestion for a complaint was made: by the AI or by keyword rules, and the AI's summary."""

    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), unique=True)
    source: Mapped[str] = mapped_column(String(10))  # "ai" or "rules"
    model: Mapped[Optional[str]] = mapped_column(String(80))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(String(200))  # why the AI was not used, if it failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

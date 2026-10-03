"""Everything a citizen or officer can do with a complaint.

Each function takes the signed-in user (`actor`), checks the role, does one unit of work,
and returns plain read-only objects. The Streamlit pages call these and never touch the database.
"""
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from .. import db
from ..constants import DEPARTMENT_BY_CATEGORY, STATUSES
from ..errors import ConflictError, NotFoundError, PermissionDenied, ServiceError
from ..models import Complaint, Department, StatusEvent, utcnow
from ..rules import suggest_category, suggest_urgency
from ..schemas import AssignIn, ComplaintCreate, ComplaintOut, DepartmentOut, EventOut, StatusIn, UserOut
from ..workflow import can_assign, can_move, make_ref


def _require(actor: UserOut, role: str) -> None:
    if actor.role != role:
        raise PermissionDenied(f"This action is for {role}s only.")


def _view(c: Complaint) -> ComplaintOut:
    return ComplaintOut(
        ref=c.ref,
        description=c.description,
        area=c.area,
        latitude=c.latitude,
        longitude=c.longitude,
        status=c.status,
        suggested_category=c.suggested_category,
        suggested_urgency=c.suggested_urgency,
        category=c.category,
        urgency=c.urgency,
        department=c.department.name if c.department else None,
        reporter_name=c.reporter.full_name if c.reporter else None,
        created_at=c.created_at,
        events=[EventOut.model_validate(e) for e in c.events],
    )


def _load(s: Session, ref: str) -> Complaint:
    c = s.scalar(select(Complaint).where(Complaint.ref == ref.strip().upper()))
    if c is None:
        raise NotFoundError("Complaint not found.")
    return c


def _with_note(base: str, note: Optional[str]) -> str:
    return f"{base} {note.strip()}" if note and note.strip() else base


def list_departments() -> list[DepartmentOut]:
    with db.session_scope() as s:
        return [DepartmentOut.model_validate(d) for d in s.scalars(select(Department).order_by(Department.name))]


# ---------- citizen ----------

def submit(actor: UserOut, data: ComplaintCreate) -> ComplaintOut:
    _require(actor, "citizen")
    with db.session_scope() as s:
        c = Complaint(
            reporter_id=actor.id,
            description=data.description,
            area=data.area,
            latitude=data.latitude,
            longitude=data.longitude,
            status="Submitted",
            suggested_category=suggest_category(data.description),
            suggested_urgency=suggest_urgency(data.description),
        )
        s.add(c)
        s.flush()  # gives the row its id
        c.ref = make_ref(c.id)
        c.events.append(StatusEvent(status="Submitted", note="Reported.", actor_id=actor.id))
        s.flush()  # fills in timestamps before we build the view
        return _view(c)


def list_mine(actor: UserOut) -> list[ComplaintOut]:
    _require(actor, "citizen")
    with db.session_scope() as s:
        rows = s.scalars(
            select(Complaint)
            .where(Complaint.reporter_id == actor.id)
            .options(selectinload(Complaint.events), selectinload(Complaint.department), selectinload(Complaint.reporter))
            .order_by(Complaint.id.desc())
        )
        return [_view(c) for c in rows]


def get(actor: UserOut, ref: str) -> ComplaintOut:
    with db.session_scope() as s:
        c = _load(s, ref)
        if actor.role != "officer" and c.reporter_id != actor.id:
            raise NotFoundError("Complaint not found.")  # not "forbidden", so references cannot be guessed
        return _view(c)


# ---------- officer ----------

def queue(actor: UserOut, status: Optional[str] = None, limit: int = 200, offset: int = 0) -> list[ComplaintOut]:
    """Needs review first, then open work, then resolved. Within a group: most urgent, then oldest."""
    _require(actor, "officer")
    if status is not None and status not in STATUSES:
        raise ServiceError(f"Unknown status: {status}")
    status_rank = case(
        (Complaint.status == "Submitted", 0),
        (Complaint.status == "Assigned", 1),
        (Complaint.status == "In Progress", 2),
        else_=3,
    )
    urgency = func.coalesce(Complaint.urgency, Complaint.suggested_urgency)
    urgency_rank = case((urgency == "High", 0), (urgency == "Medium", 1), else_=2)
    stmt = (
        select(Complaint)
        .options(selectinload(Complaint.events), selectinload(Complaint.department), selectinload(Complaint.reporter))
        .order_by(status_rank, urgency_rank, Complaint.id)
        .limit(limit)
        .offset(offset)
    )
    if status:
        stmt = stmt.where(Complaint.status == status)
    with db.session_scope() as s:
        return [_view(c) for c in s.scalars(stmt)]


def assign(actor: UserOut, ref: str, data: AssignIn) -> ComplaintOut:
    """Verify and assign. The officer's category and urgency become the record; the suggestions stay as they were."""
    _require(actor, "officer")
    with db.session_scope() as s:
        c = _load(s, ref)
        if not can_assign(c.status):
            raise ConflictError(f"This complaint is already {c.status}.")
        if data.department_id is not None:
            dept = s.get(Department, data.department_id)
        else:
            dept = s.scalar(select(Department).where(Department.name == DEPARTMENT_BY_CATEGORY[data.category]))
        if dept is None:
            raise ServiceError("Unknown department.")
        c.category, c.urgency, c.department = data.category, data.urgency, dept
        c.status, c.updated_at = "Assigned", utcnow()
        c.events.append(
            StatusEvent(status="Assigned", note=_with_note(f"Reviewed and assigned to {dept.name}.", data.note), actor_id=actor.id)
        )
        s.flush()
        return _view(c)


def move_status(actor: UserOut, ref: str, data: StatusIn) -> ComplaintOut:
    _require(actor, "officer")
    with db.session_scope() as s:
        c = _load(s, ref)
        if not can_move(c.status, data.status):
            raise ConflictError(f"Cannot move from {c.status} to {data.status}.")
        c.status, c.updated_at = data.status, utcnow()
        base = "Work started." if data.status == "In Progress" else "Resolved."
        c.events.append(StatusEvent(status=data.status, note=_with_note(base, data.note), actor_id=actor.id))
        s.flush()
        return _view(c)

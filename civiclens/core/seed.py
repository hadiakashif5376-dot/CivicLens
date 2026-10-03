from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import DEPARTMENT_BY_CATEGORY
from .models import Department, User
from .security import hash_password


def seed(session: Session, officer_email: str = "", officer_password: str = "") -> None:
    """Create the departments, and the first officer if credentials were provided.

    There is deliberately no default officer password: this repository is public on GitHub.
    An existing officer is left alone, so changing the secret later does not change their password.
    """
    existing = set(session.scalars(select(Department.name)))
    for name in DEPARTMENT_BY_CATEGORY.values():
        if name not in existing:
            session.add(Department(name=name))
    if officer_email and officer_password:
        if session.scalar(select(User).where(User.email == officer_email)) is None:
            session.add(
                User(email=officer_email, full_name="Duty Officer", role="officer", password_hash=hash_password(officer_password))
            )

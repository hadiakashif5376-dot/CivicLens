from sqlalchemy import select

from .. import db
from ..errors import AuthError, ConflictError
from ..models import User
from ..schemas import RegisterIn, UserOut
from ..security import DUMMY_HASH, hash_password, verify_password


def register_citizen(data: RegisterIn) -> UserOut:
    """Public sign-up always creates a citizen. Officers are created by an admin, never here."""
    with db.session_scope() as s:
        if s.scalar(select(User).where(User.email == data.email)) is not None:
            raise ConflictError("An account with this email already exists.")
        user = User(email=data.email, full_name=data.full_name.strip(), role="citizen", password_hash=hash_password(data.password))
        s.add(user)
        s.flush()
        return UserOut.model_validate(user)


def authenticate(email: str, password: str) -> UserOut:
    with db.session_scope() as s:
        user = s.scalar(select(User).where(User.email == email.strip().lower()))
        ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
        if user is None or not ok:
            raise AuthError("Incorrect email or password.")
        return UserOut.model_validate(user)

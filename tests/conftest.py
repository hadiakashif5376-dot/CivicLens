import pytest

from civiclens.core import db
from civiclens.core.schemas import RegisterIn
from civiclens.core.seed import seed
from civiclens.core.services import auth

OFFICER_EMAIL = "officer@example.com"
OFFICER_PASSWORD = "officer-test-pass"


@pytest.fixture(autouse=True)
def database():
    """A fresh in-memory database for every test."""
    db.configure("sqlite://", force=True)
    db.create_tables()
    with db.session_scope() as s:
        seed(s, OFFICER_EMAIL, OFFICER_PASSWORD)
    yield
    db.drop_tables()


def make_citizen(email="resident@example.com"):
    auth.register_citizen(RegisterIn(email=email, full_name="Test Resident", password="resident-pass-1"))
    return auth.authenticate(email, "resident-pass-1")


@pytest.fixture()
def citizen():
    return make_citizen()


@pytest.fixture()
def officer():
    return auth.authenticate(OFFICER_EMAIL, OFFICER_PASSWORD)

"""End-to-end behaviour of the services against an in-memory database."""
import pytest

from civiclens.core.errors import AuthError, ConflictError, NotFoundError, PermissionDenied, ServiceError
from civiclens.core.schemas import AssignIn, ComplaintCreate, RegisterIn, StatusIn
from civiclens.core.services import auth, complaints

from .conftest import make_citizen

DRAIN = ComplaintCreate(
    description="Blocked drain with standing water near the school gate.", area="Madina Town", latitude=31.418, longitude=73.112
)


def test_register_always_creates_a_citizen():
    user = auth.register_citizen(RegisterIn(email="a@example.com", full_name="A", password="longenough1"))
    assert user.role == "citizen"


def test_duplicate_email_is_rejected(citizen):
    with pytest.raises(ConflictError):
        auth.register_citizen(RegisterIn(email="RESIDENT@example.com", full_name="B", password="longenough1"))


def test_wrong_password_is_rejected(citizen):
    with pytest.raises(AuthError):
        auth.authenticate("resident@example.com", "wrong-password")
    with pytest.raises(AuthError):
        auth.authenticate("nobody@example.com", "whatever-it-is")


def test_submit_creates_reference_suggestions_and_first_event(citizen):
    c = complaints.submit(citizen, DRAIN)
    assert c.ref.startswith("SC-")
    assert c.status == "Submitted"
    assert c.suggested_category == "Drainage"
    assert c.suggested_urgency == "High"  # "school" is a high-urgency word
    assert c.category is None and c.urgency is None  # nothing is confirmed yet
    assert [e.status for e in c.events] == ["Submitted"]


def test_citizen_sees_only_their_own_complaints(citizen):
    mine = complaints.submit(citizen, DRAIN)
    other = make_citizen("other@example.com")
    theirs = complaints.submit(other, DRAIN.model_copy(update={"description": "Pothole on the main road near the market."}))
    assert [c.ref for c in complaints.list_mine(citizen)] == [mine.ref]
    with pytest.raises(NotFoundError):
        complaints.get(citizen, theirs.ref)


def test_citizen_cannot_use_officer_actions(citizen):
    c = complaints.submit(citizen, DRAIN)
    with pytest.raises(PermissionDenied):
        complaints.queue(citizen)
    with pytest.raises(PermissionDenied):
        complaints.assign(citizen, c.ref, AssignIn(category="Drainage", urgency="High"))


def test_officer_cannot_submit_complaints(officer):
    with pytest.raises(PermissionDenied):
        complaints.submit(officer, DRAIN)


def test_queue_puts_unreviewed_and_urgent_first(citizen, officer):
    low = complaints.submit(citizen, DRAIN.model_copy(update={"description": "Streetlight is not working on my corner."}))
    high = complaints.submit(citizen, DRAIN)
    assert [c.ref for c in complaints.queue(officer)] == [high.ref, low.ref]
    assert [c.ref for c in complaints.queue(officer, status="Submitted")] == [high.ref, low.ref]
    with pytest.raises(ServiceError):
        complaints.queue(officer, status="Nonsense")


def test_officer_can_change_the_suggestion_when_assigning(citizen, officer):
    c = complaints.submit(citizen, DRAIN)
    updated = complaints.assign(officer, c.ref, AssignIn(category="Waste management", urgency="Medium", note="Crew visits today."))
    assert updated.status == "Assigned"
    assert (updated.category, updated.urgency) == ("Waste management", "Medium")
    assert updated.suggested_category == "Drainage"  # the suggestion is kept as it was
    assert updated.department == "Sanitation"
    assert "Crew visits today." in updated.events[-1].note


def test_complaint_cannot_be_assigned_twice(citizen, officer):
    c = complaints.submit(citizen, DRAIN)
    complaints.assign(officer, c.ref, AssignIn(category="Drainage", urgency="High"))
    with pytest.raises(ConflictError):
        complaints.assign(officer, c.ref, AssignIn(category="Drainage", urgency="High"))


def test_full_lifecycle_is_visible_to_the_citizen(citizen, officer):
    c = complaints.submit(citizen, DRAIN)
    complaints.assign(officer, c.ref, AssignIn(category="Drainage", urgency="High"))
    complaints.move_status(officer, c.ref, StatusIn(status="In Progress"))
    complaints.move_status(officer, c.ref, StatusIn(status="Resolved", note="Drain cleared."))
    seen = complaints.get(citizen, c.ref)
    assert seen.status == "Resolved"
    assert [e.status for e in seen.events] == ["Submitted", "Assigned", "In Progress", "Resolved"]


def test_status_cannot_skip_steps(citizen, officer):
    c = complaints.submit(citizen, DRAIN)
    with pytest.raises(ConflictError):
        complaints.move_status(officer, c.ref, StatusIn(status="Resolved"))

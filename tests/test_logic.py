"""Tests for the parts that need no database and no Streamlit."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from civiclens.core import config, security
from civiclens.core.errors import validation_message
from civiclens.core.rules import suggest_category, suggest_urgency
from civiclens.core.schemas import AssignIn, ComplaintCreate, RegisterIn
from civiclens.core.workflow import can_assign, can_move, make_ref
from civiclens.ui.format import fmt_time, md_escape


def test_category_rules_match_the_prototype():
    assert suggest_category("Blocked drain with standing water") == "Drainage"
    assert suggest_category("Garbage bins are full") == "Waste management"
    assert suggest_category("Large pothole near the market") == "Roads"
    assert suggest_category("No water supply since yesterday") == "Water supply"
    assert suggest_category("Streetlight is not working") == "Streetlights"
    assert suggest_category("Exposed wire hanging low") == "Public safety"
    assert suggest_category("Noisy neighbours") == "Other"


def test_urgency_rules_match_the_prototype():
    assert suggest_urgency("Water near the school gate") == "High"
    assert suggest_urgency("Pothole on the road") == "Medium"
    assert suggest_urgency("Streetlight is not working") == "Low"


def test_workflow_only_moves_forward_one_step():
    assert can_assign("Submitted") and not can_assign("Assigned")
    assert can_move("Assigned", "In Progress") and can_move("In Progress", "Resolved")
    assert not can_move("Submitted", "Resolved")
    assert not can_move("Assigned", "Resolved")
    assert not can_move("Resolved", "In Progress")


def test_reference_format():
    assert make_ref(1) == "SC-1001"
    assert make_ref(250) == "SC-1250"


def test_password_hash_round_trip():
    stored = security.hash_password("a-good-password")
    assert stored != "a-good-password"
    assert security.verify_password("a-good-password", stored)
    assert not security.verify_password("another-password", stored)
    assert not security.verify_password("anything", "not-a-valid-hash")


def test_schemas_validate_and_clean_input():
    ok = ComplaintCreate(description="  Blocked drain near school  ", area=" Madina Town ", latitude=31.4, longitude=73.1)
    assert ok.description == "Blocked drain near school" and ok.area == "Madina Town"
    assert RegisterIn(email=" A@Example.COM ", full_name="A", password="longenough1").email == "a@example.com"
    for bad in (
        lambda: ComplaintCreate(description="x", latitude=31.4, longitude=73.1),
        lambda: ComplaintCreate(description="  x  ", latitude=31.4, longitude=73.1),  # padding cannot beat the length rule
        lambda: ComplaintCreate(description="Valid description", latitude=95, longitude=73.1),
        lambda: AssignIn(category="Made up", urgency="High"),
        lambda: RegisterIn(email="not-an-email", full_name="A", password="longenough1"),
    ):
        with pytest.raises(ValidationError):
            bad()


def test_validation_message_is_one_readable_line():
    with pytest.raises(ValidationError) as caught:
        ComplaintCreate(description="x", latitude=31.4, longitude=73.1)
    message = validation_message(caught.value)
    assert message.startswith("Description:") and "\n" not in message


def test_settings_have_no_default_officer_password():
    s = config.from_mapping({})
    assert s.officer_email == "" and s.officer_password == ""
    assert s.is_demo_storage
    s = config.from_mapping({"DATABASE_URL": "postgresql://u:p@host/db", "OFFICER_EMAIL": " Boss@Example.com "})
    assert not s.is_demo_storage and s.officer_email == "boss@example.com"


def test_markdown_in_citizen_text_is_neutralised():
    shown = md_escape("[click here](https://evil.example) **bold** <b>x</b> ![img](http://x)")
    assert "\\[click here\\]\\(" in shown
    assert "\\*\\*bold\\*\\*" in shown
    assert md_escape(None) == ""


def test_times_are_shown_in_the_configured_zone():
    stamp = datetime(2026, 10, 3, 19, 0, tzinfo=timezone.utc)
    assert fmt_time(stamp, "Asia/Karachi") == "04 Oct 2026, 00:00"
    assert fmt_time(stamp.replace(tzinfo=None), "Asia/Karachi") == "04 Oct 2026, 00:00"  # naive means UTC
    assert fmt_time(stamp, "Not/AZone") == "03 Oct 2026, 19:00"  # unknown zone falls back to UTC
    assert fmt_time(None) == ""

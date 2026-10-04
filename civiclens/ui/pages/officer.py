"""The officer's single screen: overview and map on top, queue and the selected complaint below."""
import pandas as pd
import streamlit as st
from pydantic import ValidationError

from ...core.config import Settings
from ...core.constants import CATEGORIES, URGENCIES
from ...core.errors import ServiceError, validation_message
from ...core.schemas import AssignIn, ComplaintOut, StatusIn, UserOut
from ...core.services import complaints
from .. import components, session
from ..format import fmt_time, md_escape

_SELECTED = "selected_ref"
_VIEWS = ["All", "Needs review", "Open"]
_DEFAULT_TEAM = "Default team for the category"


def render(user: UserOut, settings: Settings) -> None:
    st.title("Complaint queue")
    session.show_flash()
    rows = complaints.queue(user)
    _overview(rows)
    st.divider()
    _queue_and_workspace(user, rows, settings)


def _overview(rows: list[ComplaintOut]) -> None:
    open_rows = [c for c in rows if c.status != "Resolved"]
    needs_review = sum(1 for c in rows if c.status == "Submitted")
    high = sum(1 for c in open_rows if components.effective_urgency(c) == "High")
    a, b, c_ = st.columns(3)
    a.metric("Open complaints", len(open_rows))
    b.metric("High urgency and open", high)
    c_.metric("Needs review", needs_review)

    if open_rows:
        points = pd.DataFrame(
            {
                "latitude": [c.latitude for c in open_rows],
                "longitude": [c.longitude for c in open_rows],
                "color": [components.URGENCY_HEX[components.effective_urgency(c)] for c in open_rows],
            }
        )
        st.map(points, latitude="latitude", longitude="longitude", color="color", size=40)
        st.caption("Open complaints. Red is high urgency, blue is medium, green is low.")
    else:
        st.info("No open complaints.")


def _queue_and_workspace(user: UserOut, rows: list[ComplaintOut], settings: Settings) -> None:
    view = st.radio("Show", _VIEWS, horizontal=True)
    if view == "Needs review":
        shown = [c for c in rows if c.status == "Submitted"]
    elif view == "Open":
        shown = [c for c in rows if c.status != "Resolved"]
    else:
        shown = rows
    if not shown:
        st.info("No complaints in this view.")
        return

    table = pd.DataFrame(
        {
            "Ref": [c.ref for c in shown],
            "Urgency": [components.effective_urgency(c) for c in shown],
            "Status": [c.status for c in shown],
            "Area": [c.area or "" for c in shown],
            "Category": [components.effective_category(c) for c in shown],
            "Reported": [fmt_time(c.created_at, settings.display_tz) for c in shown],
        }
    )
    st.dataframe(table, hide_index=True)

    refs = [c.ref for c in shown]
    by_ref = {c.ref: c for c in shown}
    remembered = st.session_state.get(_SELECTED)
    ref = st.selectbox(
        "Open a complaint",
        refs,
        index=refs.index(remembered) if remembered in refs else 0,
        format_func=lambda r: f"{r} · {components.effective_urgency(by_ref[r])} · {by_ref[r].status} · {by_ref[r].area or ''}",
    )
    st.session_state[_SELECTED] = ref
    _workspace(user, by_ref[ref], settings)


def _workspace(user: UserOut, c: ComplaintOut, settings: Settings) -> None:
    with st.container(border=True):
        st.markdown(f"### {c.ref} · {components.status_tag(c.status)}")
        st.caption(f"{md_escape(c.area)} · reported by {md_escape(c.reporter_name)} · {fmt_time(c.created_at, settings.display_tz)}")
        st.link_button(
            "Open location in maps",
            f"https://www.openstreetmap.org/?mlat={c.latitude}&mlon={c.longitude}#map=18/{c.latitude}/{c.longitude}",
        )
        components.point_map(c.latitude, c.longitude)
        st.markdown(md_escape(c.description))
        components.understood(c)
        with st.expander("Timeline"):
            components.timeline(c, settings.display_tz)

        st.markdown("#### Verify, assign and track")
        if c.status == "Submitted":
            _assign_form(user, c)
        elif c.status in ("Assigned", "In Progress"):
            _progress_controls(user, c)
        else:
            st.write("This complaint is resolved.")


def _assign_form(user: UserOut, c: ComplaintOut) -> None:
    departments = complaints.list_departments()
    team_ids = {d.name: d.id for d in departments}
    category = c.suggested_category if c.suggested_category in CATEGORIES else "Other"
    urgency = c.suggested_urgency if c.suggested_urgency in URGENCIES else "Low"
    st.caption("Category and urgency are suggested by keyword rules. Change them if they look wrong.")
    with st.form(f"assign_{c.ref}"):
        col1, col2, col3 = st.columns(3)
        new_category = col1.selectbox("Category", CATEGORIES, index=CATEGORIES.index(category))
        new_urgency = col2.selectbox("Urgency", URGENCIES, index=URGENCIES.index(urgency))
        team = col3.selectbox("Team", [_DEFAULT_TEAM] + list(team_ids))
        note = st.text_input("Message to the citizen (optional)")
        go = st.form_submit_button("Confirm and assign", type="primary")
    if not go:
        return
    try:
        updated = complaints.assign(
            user,
            c.ref,
            AssignIn(category=new_category, urgency=new_urgency, department_id=team_ids.get(team), note=note or None),
        )
    except ValidationError as exc:
        st.error(validation_message(exc))
    except ServiceError as exc:
        st.error(str(exc))
    else:
        session.flash(f"{updated.ref} assigned to {updated.department}.")
        st.rerun()


def _progress_controls(user: UserOut, c: ComplaintOut) -> None:
    next_status, label = ("In Progress", "Mark in progress") if c.status == "Assigned" else ("Resolved", "Mark resolved")
    note = st.text_input("Update for the citizen (optional)", key=f"note_{c.ref}_{c.status}")
    if st.button(label, type="primary", key=f"move_{c.ref}_{c.status}"):
        try:
            complaints.move_status(user, c.ref, StatusIn(status=next_status, note=note or None))
        except ValidationError as exc:
            st.error(validation_message(exc))
        except ServiceError as exc:
            st.error(str(exc))
        else:
            session.flash(f"{c.ref} is now {next_status}.")
            st.rerun()

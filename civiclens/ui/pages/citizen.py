"""The citizen's single screen: send a complaint on the left, follow your complaints on the right."""
import streamlit as st
from pydantic import ValidationError

from ...core.config import Settings
from ...core.errors import ServiceError, validation_message
from ...core.schemas import ComplaintCreate, ComplaintOut, UserOut
from ...core.services import complaints
from .. import components, location, session
from ..format import md_escape


def render(user: UserOut, settings: Settings) -> None:
    st.title("Report a problem")
    session.show_flash()
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        _form(user)
    with right:
        _my_complaints(user, settings)


def _form(user: UserOut) -> None:
    st.subheader("New complaint")
    place = location.pick_location()  # outside the form so the location button updates the page immediately

    with st.form(f"new_complaint_{session.form_nonce()}"):
        description = st.text_area(
            "What is the problem?",
            placeholder="Example: Blocked drain with standing water near the school gate...",
            height=140,
            max_chars=2000,
        )
        submitted = st.form_submit_button("Send complaint", type="primary")
        st.caption("For an emergency, call your local emergency number instead of using this form.")

    if not submitted:
        return
    if place is None:
        st.error("Set the location first: press the location button, or choose an area.")
        return
    try:
        created = complaints.submit(
            user,
            ComplaintCreate(description=description, area=place.area, latitude=place.latitude, longitude=place.longitude),
        )
    except ValidationError as exc:
        st.error(validation_message(exc))
    except ServiceError as exc:
        st.error(str(exc))
    else:
        session.flash(f"Complaint {created.ref} received. An officer will review it.")
        session.bump_form()
        st.rerun()


def _my_complaints(user: UserOut, settings: Settings) -> None:
    st.subheader("My complaints")
    mine = complaints.list_mine(user)
    if not mine:
        st.info("You have not sent a complaint yet. Your complaints and their progress will appear here.")
        return
    for c in mine:
        _card(c, settings)


def _card(c: ComplaintOut, settings: Settings) -> None:
    with st.container(border=True):
        head, where = st.columns([2, 1])
        head.markdown(f"**{c.ref}** · {components.status_tag(c.status)}")
        where.caption(md_escape(c.area))
        st.markdown(md_escape(c.description))
        components.progress(c.status)
        components.understood(c)
        with st.expander("Timeline"):
            components.timeline(c, settings.display_tz)

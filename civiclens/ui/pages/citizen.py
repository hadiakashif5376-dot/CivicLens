"""The citizen's single screen: send a complaint on the left, follow your complaints on the right."""
import streamlit as st
from pydantic import ValidationError

from ...core.config import Settings
from ...core.constants import AREAS
from ...core.errors import ServiceError, validation_message
from ...core.schemas import ComplaintCreate, ComplaintOut, UserOut
from ...core.services import complaints
from .. import components, session
from ..format import md_escape

_FIRST_LAT, _FIRST_LON = next(iter(AREAS.values()))


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
    with st.form(f"new_complaint_{session.form_nonce()}"):
        description = st.text_area(
            "What is the problem?",
            placeholder="Example: Blocked drain with standing water near the school gate...",
            height=140,
            max_chars=2000,
        )
        area = st.selectbox("Area", list(AREAS))
        exact = st.checkbox("Use exact coordinates instead of the area")
        lat_col, lon_col = st.columns(2)
        lat = lat_col.number_input("Latitude", value=_FIRST_LAT, format="%.6f", min_value=-90.0, max_value=90.0)
        lon = lon_col.number_input("Longitude", value=_FIRST_LON, format="%.6f", min_value=-180.0, max_value=180.0)
        submitted = st.form_submit_button("Send complaint", type="primary")
        st.caption("For an emergency, call your local emergency number instead of using this form.")

    if not submitted:
        return
    latitude, longitude = (lat, lon) if exact else AREAS[area]
    try:
        created = complaints.submit(
            user, ComplaintCreate(description=description, area=area, latitude=latitude, longitude=longitude)
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

"""Small display pieces shared by the citizen and officer screens."""
import pandas as pd
import streamlit as st

from ..core.schemas import ComplaintOut
from .format import fmt_time, md_escape

URGENCY_COLOR = {"High": "red", "Medium": "blue", "Low": "green"}
URGENCY_HEX = {"High": "#d9480f", "Medium": "#2b62ad", "Low": "#1d7a45"}
STATUS_COLOR = {"Submitted": "gray", "Assigned": "blue", "In Progress": "orange", "Resolved": "green"}
STATUS_PROGRESS = {"Submitted": 25, "Assigned": 50, "In Progress": 75, "Resolved": 100}


def urgency_tag(urgency: str) -> str:
    return f":{URGENCY_COLOR.get(urgency, 'gray')}[**{urgency}**]"


def status_tag(status: str) -> str:
    return f":{STATUS_COLOR.get(status, 'gray')}[**{status}**]"


def effective_urgency(c: ComplaintOut) -> str:
    return c.urgency or c.suggested_urgency or "Low"


def effective_category(c: ComplaintOut) -> str:
    return c.category or c.suggested_category or "Other"


def progress(status: str) -> None:
    st.progress(STATUS_PROGRESS.get(status, 0), text=status)


def understood(c: ComplaintOut) -> None:
    """Category, team and urgency, marked as suggested until an officer confirms them."""
    confirmed = c.category is not None
    suffix = "" if confirmed else " (suggested)"
    team = c.department or "To be decided by an officer"
    st.markdown(
        f"**Category** {md_escape(effective_category(c))}{suffix}  \n"
        f"**Team** {md_escape(team)}  \n"
        f"**Urgency** {urgency_tag(effective_urgency(c))}{suffix}"
    )


def timeline(c: ComplaintOut, tz_name: str) -> None:
    for event in c.events:
        st.markdown(f"`{fmt_time(event.created_at, tz_name)}`  {md_escape(event.note)}")


def point_map(lat: float, lon: float, zoom: int = 15) -> None:
    """A small map with one pin, zoomed in far enough for street and area names to show."""
    frame = pd.DataFrame({"latitude": [lat], "longitude": [lon]})
    try:
        st.map(frame, size=30, zoom=zoom)
    except TypeError:  # an older Streamlit without the zoom option
        st.map(frame, size=30)

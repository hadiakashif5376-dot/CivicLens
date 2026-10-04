"""Choosing where the problem is: an area from the list, the device's location, or typed coordinates.

This sits outside the complaint form on purpose. Widgets inside st.form do not update until the form is
submitted, and the location button needs to update the page straight away.
"""
from dataclasses import dataclass
from typing import Optional

import streamlit as st

from ..core import geocode
from ..core.constants import AREAS
from ..core.geo import nearest_area, valid_coordinates
from . import components
from .format import md_escape

_AREA, _GPS, _EXACT = "Area from the list", "My current location", "Exact coordinates"
_MODES = [_AREA, _GPS, _EXACT]
_GPS_FIX = "gps_fix"
_FIRST_LAT, _FIRST_LON = next(iter(AREAS.values()))
_MAX_AREA_TEXT = 120  # the database column holds 120 characters


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    area: str  # saved with the complaint: a place name plus how the location was set
    nearby: tuple = ()  # names of nearby areas, shown under the map
    looked_up: bool = False  # True when the names came from OpenStreetMap
    lookup_failed: bool = False


def pick_location() -> Optional[Location]:
    """Show the location controls and return the chosen place, or None if none is set yet."""
    mode = st.radio("Where is the problem?", _MODES, horizontal=True)
    if mode == _AREA:
        place = _from_area()
    elif mode == _GPS:
        place = _from_gps()
    else:
        place = _from_typed()

    if place is not None:
        components.point_map(place.latitude, place.longitude, zoom=15)
        st.caption(f"{md_escape(place.area)} · {place.latitude:.5f}, {place.longitude:.5f}")
        if place.nearby:
            st.caption("Nearby areas: " + " · ".join(md_escape(n) for n in place.nearby))
        if place.looked_up:
            st.caption("Place names from OpenStreetMap contributors.")
        elif place.lookup_failed:
            st.caption("Place name not available right now. The coordinates are still saved.")
    return place


def _from_area() -> Location:
    name = st.selectbox("Area", list(AREAS))
    lat, lon = AREAS[name]
    return Location(lat, lon, name)


def _from_typed() -> Location:
    col_lat, col_lon = st.columns(2)
    lat = col_lat.number_input("Latitude", value=_FIRST_LAT, format="%.6f", min_value=-90.0, max_value=90.0, key="exact_lat")
    lon = col_lon.number_input("Longitude", value=_FIRST_LON, format="%.6f", min_value=-180.0, max_value=180.0, key="exact_lon")
    name = nearest_area(lat, lon, AREAS)  # no online lookup here: it would fire on every keystroke
    return Location(lat, lon, f"Near {name}" if name else "Typed coordinates")


def _from_gps() -> Optional[Location]:
    st.caption(
        "Press the button below and allow location access when your browser asks. "
        "Your location is used only to send this complaint to the right team. "
        "The place name is looked up on OpenStreetMap using your coordinates."
    )
    fix = _read_device_location()
    if fix is None:
        st.info("No location yet. Press the button, or choose another way to set the location.")
        return None
    lat, lon, accuracy = fix["lat"], fix["lon"], fix.get("accuracy")
    note = f"GPS, within {round(accuracy)} m" if isinstance(accuracy, (int, float)) else "GPS"
    with st.spinner("Finding the place name..."):
        name, nearby = _describe(round(lat, 4), round(lon, 4))  # rounded to about 10 m, so repeat lookups hit the cache
    found = name is not None or bool(nearby)
    label = name or nearest_area(lat, lon, AREAS) or "Current location"
    return Location(lat, lon, _fit(label, f" ({note})"), tuple(nearby), looked_up=found, lookup_failed=not found)


@st.cache_data(ttl=900, show_spinner=False)
def _describe(lat: float, lon: float):
    return geocode.reverse_geocode(lat, lon), geocode.nearby_places(lat, lon)


def _fit(label: str, suffix: str) -> str:
    return label[: _MAX_AREA_TEXT - len(suffix)] + suffix


def _read_device_location() -> Optional[dict]:
    """Ask the browser for its position. The last good reading is kept for the rest of the session."""
    try:
        from streamlit_geolocation import streamlit_geolocation
    except ImportError:
        st.warning("The location button is not installed. Add streamlit-geolocation to requirements.txt.")
        return st.session_state.get(_GPS_FIX)

    reading = streamlit_geolocation()
    if isinstance(reading, dict) and valid_coordinates(reading.get("latitude"), reading.get("longitude")):
        st.session_state[_GPS_FIX] = {
            "lat": float(reading["latitude"]),
            "lon": float(reading["longitude"]),
            "accuracy": reading.get("accuracy"),
        }
    return st.session_state.get(_GPS_FIX)

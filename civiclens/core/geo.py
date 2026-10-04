"""Distance and nearest-area helpers. Pure Python, no Streamlit and no database."""
from math import asin, cos, radians, sin, sqrt
from typing import Mapping, Optional, Tuple

EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line distance over the earth's surface, in metres."""
    p1, p2 = radians(lat1), radians(lat2)
    d_phi = p2 - p1
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(p1) * cos(p2) * sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))


def valid_coordinates(lat, lon) -> bool:
    """True only for real numbers inside the valid latitude and longitude ranges."""
    for value in (lat, lon):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def nearest_area(lat: float, lon: float, areas: Mapping[str, Tuple[float, float]], max_m: float = 5000) -> Optional[str]:
    """Name of the closest known area, or None when every area is farther than max_m."""
    best, best_distance = None, max_m
    for name, (area_lat, area_lon) in areas.items():
        distance = haversine_m(lat, lon, area_lat, area_lon)
        if distance <= best_distance:
            best, best_distance = name, distance
    return best

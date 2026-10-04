"""Place names from OpenStreetMap's free services. Standard library only, no Streamlit.

Fair use: Nominatim allows about one request per second and asks apps to identify themselves.
That is fine for a prototype. For real traffic, run your own geocoder or use a paid one.
Every function returns None or an empty list when the network fails, so a failed lookup never breaks a complaint.
"""
import json
import urllib.parse
import urllib.request
from typing import Optional

from .geo import haversine_m, valid_coordinates

NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = "CivicLens/0.1 (city complaint prototype)"
PLACE_TYPES = "suburb|neighbourhood|quarter|village|town|hamlet"

_ROAD_KEYS = ("road", "pedestrian", "footway")
_AREA_KEYS = ("neighbourhood", "suburb", "quarter", "city_district", "residential")
_CITY_KEYS = ("city", "town", "village", "municipality")


def _first(address: dict, keys) -> Optional[str]:
    for key in keys:
        value = address.get(key)
        if value:
            return str(value)
    return None


def label_from_address(address: dict, display_name: str = "") -> str:
    """Build a short, findable label such as "Main Road, Gulshan-e-Iqbal, Karachi"."""
    parts = []
    for value in (_first(address, _ROAD_KEYS), _first(address, _AREA_KEYS), _first(address, _CITY_KEYS)):
        if value and value not in parts:
            parts.append(value)
    if parts:
        return ", ".join(parts)[:100]
    return ", ".join(p.strip() for p in display_name.split(",")[:3] if p.strip())[:100]


def _get_json(url: str, data: Optional[bytes] = None, timeout: float = 6):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def reverse_geocode(lat: float, lon: float, language: str = "en", timeout: float = 6) -> Optional[str]:
    """The place name at these coordinates, or None if the lookup fails."""
    query = urllib.parse.urlencode(
        {
            "format": "jsonv2",
            "lat": f"{lat:.6f}",
            "lon": f"{lon:.6f}",
            "zoom": 17,
            "addressdetails": 1,
            "accept-language": language,
        }
    )
    try:
        data = _get_json(f"{NOMINATIM_REVERSE}?{query}", timeout=timeout)
    except Exception:
        return None
    if not isinstance(data, dict) or "error" in data:
        return None
    return label_from_address(data.get("address") or {}, data.get("display_name") or "") or None


def overpass_query(lat: float, lon: float, radius_m: int) -> str:
    return (
        f"[out:json][timeout:8];"
        f'node(around:{int(radius_m)},{lat:.6f},{lon:.6f})[place~"^({PLACE_TYPES})$"][name];'
        f"out body 30;"
    )


def parse_places(data, lat: float, lon: float, limit: int = 5) -> list:
    """Names of the closest named places in an Overpass response, nearest first, without repeats."""
    elements = data.get("elements", []) if isinstance(data, dict) else []
    nearest = {}
    for element in elements:
        tags = element.get("tags") or {}
        name = str(tags.get("name:en") or tags.get("name") or "").strip()
        e_lat, e_lon = element.get("lat"), element.get("lon")
        if not name or not valid_coordinates(e_lat, e_lon):
            continue
        distance = haversine_m(lat, lon, e_lat, e_lon)
        if name not in nearest or distance < nearest[name]:
            nearest[name] = distance
    return [name for name, _ in sorted(nearest.items(), key=lambda item: item[1])][:limit]


def nearby_places(lat: float, lon: float, radius_m: int = 2500, limit: int = 5, timeout: float = 8) -> list:
    """Names of nearby suburbs, neighbourhoods and towns, or an empty list if the lookup fails."""
    body = urllib.parse.urlencode({"data": overpass_query(lat, lon, radius_m)}).encode()
    try:
        data = _get_json(OVERPASS, data=body, timeout=timeout)
    except Exception:
        return []
    return parse_places(data, lat, lon, limit)

from unittest.mock import patch

from civiclens.core import geocode


def test_label_uses_road_area_and_city():
    address = {"road": "Main Road", "suburb": "Gulshan-e-Iqbal", "city": "Karachi", "country": "Pakistan"}
    assert geocode.label_from_address(address) == "Main Road, Gulshan-e-Iqbal, Karachi"


def test_label_skips_missing_parts_and_repeats():
    assert geocode.label_from_address({"neighbourhood": "Block 5", "city": "Karachi"}) == "Block 5, Karachi"
    assert geocode.label_from_address({"suburb": "Karachi", "city": "Karachi"}) == "Karachi"


def test_label_falls_back_to_the_display_name():
    assert geocode.label_from_address({}, "Alpha, Beta, Gamma, Delta") == "Alpha, Beta, Gamma"
    assert geocode.label_from_address({}, "") == ""


def test_parse_places_sorts_by_distance_and_drops_repeats():
    data = {
        "elements": [
            {"lat": 24.9100, "lon": 67.0900, "tags": {"name": "Far Town", "place": "town"}},
            {"lat": 24.8610, "lon": 67.0110, "tags": {"name": "Near Block", "place": "neighbourhood"}},
            {"lat": 24.8650, "lon": 67.0150, "tags": {"name": "Near Block", "place": "neighbourhood"}},  # same name, farther
            {"lat": 24.8620, "lon": 67.0120, "tags": {"name:en": "Mid Colony", "name": "کالونی", "place": "suburb"}},
            {"lat": 24.8600, "lon": 67.0100, "tags": {"place": "suburb"}},  # no name
            {"lat": None, "lon": 67.0, "tags": {"name": "Broken"}},  # no usable coordinates
        ]
    }
    assert geocode.parse_places(data, 24.8607, 67.0104) == ["Near Block", "Mid Colony", "Far Town"]
    assert geocode.parse_places(data, 24.8607, 67.0104, limit=2) == ["Near Block", "Mid Colony"]


def test_parse_places_copes_with_odd_responses():
    assert geocode.parse_places(None, 1, 1) == []
    assert geocode.parse_places({}, 1, 1) == []
    assert geocode.parse_places({"elements": [{"tags": None}]}, 1, 1) == []


def test_overpass_query_contains_the_search_area():
    query = geocode.overpass_query(24.8607, 67.0104, 2500)
    assert "around:2500,24.860700,67.010400" in query
    assert "suburb|neighbourhood" in query and "[out:json]" in query


def test_reverse_geocode_returns_a_label():
    reply = {"display_name": "x", "address": {"road": "Main Road", "city": "Karachi"}}
    with patch.object(geocode, "_get_json", return_value=reply):
        assert geocode.reverse_geocode(24.86, 67.01) == "Main Road, Karachi"


def test_lookups_fail_quietly_when_the_network_is_down():
    with patch.object(geocode, "_get_json", side_effect=OSError("no network")):
        assert geocode.reverse_geocode(24.86, 67.01) is None
        assert geocode.nearby_places(24.86, 67.01) == []


def test_reverse_geocode_handles_an_error_reply():
    with patch.object(geocode, "_get_json", return_value={"error": "Unable to geocode"}):
        assert geocode.reverse_geocode(0.0, 0.0) is None

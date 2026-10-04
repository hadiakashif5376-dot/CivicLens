from civiclens.core.constants import AREAS
from civiclens.core.geo import haversine_m, nearest_area, valid_coordinates


def test_one_degree_of_latitude_is_about_111_km():
    assert abs(haversine_m(0, 0, 1, 0) - 111_195) < 300


def test_distance_to_the_same_point_is_zero():
    assert haversine_m(31.418, 73.112, 31.418, 73.112) == 0


def test_nearest_area_picks_the_closest_known_area():
    assert nearest_area(31.4182, 73.1121, AREAS) == "Madina Town"
    assert nearest_area(31.4270, 73.0925, AREAS) == "People's Colony"


def test_nearest_area_is_none_when_everything_is_far_away():
    assert nearest_area(24.86, 67.00, AREAS) is None  # a different city, hundreds of km away


def test_coordinate_validation():
    assert valid_coordinates(31.4, 73.1)
    assert valid_coordinates(0, 0)
    assert not valid_coordinates(95, 0)
    assert not valid_coordinates(0, 181)
    assert not valid_coordinates(None, 73.1)
    assert not valid_coordinates("31.4", "73.1")
    assert not valid_coordinates(True, False)
    assert not valid_coordinates(float("nan"), 1.0)

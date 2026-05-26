"""Tests for maneuver_mapper — OSRM type+modifier → Valhalla numeric type."""

import pytest
from routing_plan.core.maneuver_mapper import osrm_to_valhalla_type


@pytest.mark.parametrize(
    "osrm_type,modifier,expected",
    [
        ("depart", None, 1),
        ("arrive", None, 4),
        ("turn", "left", 16),
        ("turn", "right", 11),
        ("turn", "sharp left", 15),
        ("turn", "sharp right", 12),
        ("turn", "slight left", 17),
        ("turn", "slight right", 10),
        ("turn", "uturn", 14),
        ("continue", None, 9),
        ("new name", None, 9),
        ("notification", None, 9),
        ("merge", None, 23),
        ("on ramp", "left", 20),
        ("on ramp", "right", 18),
        ("on ramp", "straight", 18),
        ("on ramp", None, 18),
        ("off ramp", "left", 20),
        ("off ramp", "right", 18),
        ("off ramp", None, 19),
        ("fork", "left", 17),
        ("fork", "right", 10),
        ("fork", "slight left", 17),
        ("fork", "slight right", 10),
        ("end of road", "left", 16),
        ("end of road", "right", 11),
        ("roundabout", None, 26),
        ("rotary", None, 26),
        ("exit roundabout", None, 27),
        ("exit rotary", None, 27),
        ("roundabout turn", "left", 16),
        ("roundabout turn", "right", 11),
        ("unknown_type", None, 0),
    ],
)
def test_osrm_to_valhalla_type(osrm_type, modifier, expected):
    assert osrm_to_valhalla_type(osrm_type, modifier) == expected


def test_case_insensitive():
    assert osrm_to_valhalla_type("TURN", "LEFT") == 16
    assert osrm_to_valhalla_type(" Turn ", " Left ") == 16


def test_empty_strings():
    assert osrm_to_valhalla_type("", None) == 0
    assert osrm_to_valhalla_type(None, None) == 0  # type: ignore

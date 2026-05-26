"""Tests for locate_renderer — build_locate_point_layer / build_input_marker_layer."""

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "valhalla_locate_response.json"


@pytest.fixture
def response():
    with open(FIXTURE) as f:
        return json.load(f)


def test_build_locate_point_layer_valhalla(response):
    from routing_plan.core.locate_renderer import build_locate_point_layer
    layer = build_locate_point_layer(response, "valhalla")
    assert layer is not None


def test_build_locate_point_layer_osrm():
    from routing_plan.core.locate_renderer import build_locate_point_layer
    osrm_resp = {
        "results": [
            {"input_lat": 52.5, "input_lon": 13.4, "lat": 52.5001,
             "lon": 13.4001, "name": "Street", "distance_m": 5.0,
             "hint": "abc123", "way_ids": [1, 2]}
        ]
    }
    layer = build_locate_point_layer(osrm_resp, "osrm")
    assert layer is not None


def test_build_input_marker_layer():
    from routing_plan.core.locate_renderer import build_input_marker_layer
    layer = build_input_marker_layer(-6.2088, 106.8456)
    assert layer is not None

"""Tests for isochrone_renderer — build_isochrone_layer.

Feed a Valhalla isochrone GeoJSON fixture and assert the returned
QgsVectorLayer is created without error.
"""

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "valhalla_isochrone_response.json"


@pytest.fixture
def response():
    with open(FIXTURE) as f:
        return json.load(f)


def test_build_isochrone_layer_returns_layer(response):
    from routing_plan.core.isochrone_renderer import build_isochrone_layer
    layer = build_isochrone_layer(response)
    assert layer is not None


def test_build_isochrone_layer_with_name(response):
    from routing_plan.core.isochrone_renderer import build_isochrone_layer
    layer = build_isochrone_layer(response, "Test Isochrones")
    assert layer is not None


def test_returns_none_for_empty():
    from routing_plan.core.isochrone_renderer import build_isochrone_layer
    result = build_isochrone_layer({"features": []})
    assert result is None

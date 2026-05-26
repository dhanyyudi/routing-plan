"""Tests for matrix_renderer — build_matrix_table and build_matrix_lines."""

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "valhalla_matrix_response.json"


@pytest.fixture
def response():
    with open(FIXTURE) as f:
        return json.load(f)


@pytest.fixture
def sources():
    """Return Waypoint-like objects with .lon, .lat, .name attrs."""
    from routing_plan.core.waypoint_loader import Waypoint
    return [
        Waypoint(lat=-6.2088, lon=106.8456, name="Jakarta"),
        Waypoint(lat=-6.1754, lon=106.8272, name="Monas"),
    ]


@pytest.fixture
def targets():
    from routing_plan.core.waypoint_loader import Waypoint
    return [
        Waypoint(lat=-6.2088, lon=106.8456, name="Jakarta"),
        Waypoint(lat=-6.1754, lon=106.8272, name="Monas"),
        Waypoint(lat=-6.1944, lon=106.8225, name="Bundaran HI"),
    ]


def test_build_matrix_table_returns_layer(response, sources, targets):
    from routing_plan.core.matrix_renderer import build_matrix_table
    layer = build_matrix_table(response, sources, targets)
    assert layer is not None


def test_build_matrix_lines_returns_layer(response, sources, targets):
    from routing_plan.core.matrix_renderer import build_matrix_lines
    layer = build_matrix_lines(response, sources, targets)
    assert layer is not None


def test_matrix_table_empty_sources(targets):
    from routing_plan.core.matrix_renderer import build_matrix_table
    layer = build_matrix_table({"sources_to_targets": []}, [], targets)
    assert layer is not None

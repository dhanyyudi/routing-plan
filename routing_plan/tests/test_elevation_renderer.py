"""Tests for elevation_renderer — build_elevation_table and compute_elevation_stats."""

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "valhalla_elevation_response.json"


@pytest.fixture
def response():
    with open(FIXTURE) as f:
        return json.load(f)


def test_build_elevation_table_returns_layer(response):
    from routing_plan.core.elevation_renderer import build_elevation_table
    layer = build_elevation_table(response)
    assert layer is not None


def test_compute_elevation_stats(response):
    from routing_plan.core.elevation_renderer import compute_elevation_stats
    stats = compute_elevation_stats(response)
    assert "min" in stats
    assert "max" in stats
    assert "total_ascent" in stats
    assert "total_descent" in stats
    assert stats["min"] == 750
    assert stats["max"] == 910


def test_compute_elevation_stats_empty():
    from routing_plan.core.elevation_renderer import compute_elevation_stats
    result = compute_elevation_stats({"range_height": []})
    assert result["min"] == 0.0
    assert result["max"] == 0.0
    assert result["total_ascent"] == 0.0
    assert result["total_descent"] == 0.0

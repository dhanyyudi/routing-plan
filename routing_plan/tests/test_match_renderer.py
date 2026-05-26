"""Tests for match_renderer — build_matched_route_layer / build_attributes_table."""

import json
from pathlib import Path

import pytest

FIXTURE_TRACE = Path(__file__).parent / "fixtures" / "valhalla_trace_route_response.json"
FIXTURE_ATTRS = Path(__file__).parent / "fixtures" / "valhalla_trace_attributes_response.json"


@pytest.fixture
def trace_response():
    with open(FIXTURE_TRACE) as f:
        return json.load(f)


@pytest.fixture
def attrs_response():
    with open(FIXTURE_ATTRS) as f:
        return json.load(f)


def test_build_matched_route_layer(trace_response):
    from routing_plan.core.match_renderer import build_matched_route_layer
    layer = build_matched_route_layer(trace_response)
    assert layer is not None


def test_build_attributes_table(attrs_response):
    from routing_plan.core.match_renderer import build_attributes_table
    layer = build_attributes_table(attrs_response)
    assert layer is not None

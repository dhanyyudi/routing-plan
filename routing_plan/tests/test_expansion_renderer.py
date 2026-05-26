"""Tests for expansion_renderer — build_expansion_layer."""

import json
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "valhalla_expansion_response.json"


@pytest.fixture
def response():
    with open(FIXTURE) as f:
        return json.load(f)


def test_build_expansion_layer_returns_layer(response):
    from routing_plan.core.expansion_renderer import build_expansion_layer
    layer = build_expansion_layer(response)
    assert layer is not None


def test_build_expansion_layer_empty_features():
    from routing_plan.core.expansion_renderer import build_expansion_layer
    # Even with empty features, the renderer returns a (possibly empty) layer.
    result = build_expansion_layer({"features": []})
    assert result is not None

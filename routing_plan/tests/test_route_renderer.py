import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
    MOCK_RESPONSE = json.load(f)

from routing_plan.core.route_renderer import (  # noqa: E402
    ROUTE_COLOR,
    ROUTE_WIDTH,
    MANEUVER_RADIUS,
    LAYER_GROUP_NAME,
)
from routing_plan.core.valhalla_client import decode_polyline6  # noqa: E402


class TestConstants:
    def test_route_color(self):
        assert ROUTE_COLOR == "#1a73e8"

    def test_route_width(self):
        assert ROUTE_WIDTH == 2.0

    def test_maneuver_radius(self):
        assert MANEUVER_RADIUS == 1.5

    def test_layer_group_name(self):
        assert LAYER_GROUP_NAME == "Routing Plan"


class TestMockDataStructure:
    def test_has_trip(self):
        assert "trip" in MOCK_RESPONSE
        assert MOCK_RESPONSE["trip"]["status"] == 0

    def test_has_locations(self):
        locs = MOCK_RESPONSE["trip"]["locations"]
        assert len(locs) == 2
        assert locs[0]["name"] == "Monas"
        assert locs[1]["name"] == "Stasiun Gambir"

    def test_has_legs(self):
        legs = MOCK_RESPONSE["trip"]["legs"]
        assert len(legs) == 1

    def test_leg_has_shape(self):
        shape = MOCK_RESPONSE["trip"]["legs"][0]["shape"]
        assert len(shape) > 100
        coords = decode_polyline6(shape)
        assert len(coords) > 10

    def test_leg_has_maneuvers(self):
        maneuvers = MOCK_RESPONSE["trip"]["legs"][0]["maneuvers"]
        assert len(maneuvers) == 4
        assert maneuvers[0]["type"] == 2
        assert maneuvers[-1]["type"] == 4

    def test_leg_has_summary(self):
        summary = MOCK_RESPONSE["trip"]["legs"][0]["summary"]
        assert "length" in summary
        assert "time" in summary
        assert summary["length"] == 4.249
        assert summary["time"] == 713.198

    def test_trip_has_summary(self):
        summary = MOCK_RESPONSE["trip"]["summary"]
        assert summary["length"] == 4.249
        assert summary["time"] == 713.198


class TestRouteLayerLogic:
    def test_shape_to_coords(self):
        legs = MOCK_RESPONSE["trip"]["legs"]
        for leg in legs:
            shape = leg["shape"]
            coords = decode_polyline6(shape)
            assert len(coords) >= 2
            for lat, lon in coords:
                assert -90 <= lat <= 90
                assert -180 <= lon <= 180

    def test_distance_conversion(self):
        summary = MOCK_RESPONSE["trip"]["legs"][0]["summary"]
        length_km = summary["length"]
        duration_min = summary["time"] / 60
        assert length_km == pytest.approx(4.249)
        assert duration_min == pytest.approx(11.887, rel=1e-3)

    def test_maneuver_coordinates(self):
        leg = MOCK_RESPONSE["trip"]["legs"][0]
        shape_str = leg["shape"]
        coords = decode_polyline6(shape_str)
        for m in leg["maneuvers"]:
            idx = m["begin_shape_index"]
            assert idx < len(coords), f"begin_shape_index {idx} >= {len(coords)}"
            lat, lon = coords[idx]
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180

    def test_maneuver_attributes(self):
        for leg in MOCK_RESPONSE["trip"]["legs"]:
            for m in leg["maneuvers"]:
                assert "type" in m
                assert "instruction" in m
                assert "length" in m
                assert "time" in m
                assert "begin_shape_index" in m
                assert isinstance(m["street_names"], list)

    def test_maneuver_length_conversion(self):
        leg = MOCK_RESPONSE["trip"]["legs"][0]
        for m in leg["maneuvers"]:
            length_m = m["length"] * 1000
            time_s = m["time"]
            assert length_m >= 0
            assert time_s >= 0

    def test_leg_label_generation(self):
        locs = MOCK_RESPONSE["trip"]["locations"]
        labels = []
        for i, leg in enumerate(MOCK_RESPONSE["trip"]["legs"]):
            parts = []
            if i < len(locs):
                parts.append(locs[i].get("name", f"WP {i}"))
            if i + 1 < len(locs):
                parts.append(locs[i + 1].get("name", f"WP {i + 1}"))
            label = " → ".join(parts) if parts else f"Leg {i}"
            labels.append(label)
        assert labels == ["Monas → Stasiun Gambir"]

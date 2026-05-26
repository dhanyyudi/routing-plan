"""Tests for OSRM response normalization (osrm_normalize.py)."""

import json
import os
import pytest
from routing_plan.core.osrm_normalize import (
    to_valhalla_route,
    to_valhalla_matrix,
    to_valhalla_trace,
    to_valhalla_locate,
)
from routing_plan.core.waypoint_loader import Waypoint


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    path = os.path.join(FIXTURE_DIR, name)
    with open(path) as f:
        return json.load(f)


class TestToValhallaRoute:
    def test_basic_route_shape(self):
        fixture = _load("osrm_route_response.json")
        wps = [
            Waypoint(lat=52.517037, lon=13.38886, name="Start"),
            Waypoint(lat=52.529407, lon=13.397634, name="Mid"),
            Waypoint(lat=52.523219, lon=13.428555, name="End"),
        ]
        result = to_valhalla_route(fixture, wps)

        assert "trip" in result
        trip = result["trip"]
        assert trip["units"] == "kilometers"
        assert len(trip["locations"]) == 3
        assert len(trip["legs"]) == 2

        # First leg
        leg0 = trip["legs"][0]
        assert "shape" in leg0
        assert leg0["summary"]["length"] > 0
        assert leg0["summary"]["time"] > 0
        assert len(leg0["maneuvers"]) == 2

        # Maneuver checks
        m0 = leg0["maneuvers"][0]
        assert m0["type"] == 1  # depart
        m1 = leg0["maneuvers"][1]
        assert m1["type"] == 11  # right turn

    def test_locations_have_names(self):
        fixture = _load("osrm_route_response.json")
        wps = [
            Waypoint(lat=52.517037, lon=13.38886, name="Start"),
            Waypoint(lat=52.529407, lon=13.397634, name="Mid"),
            Waypoint(lat=52.523219, lon=13.428555, name="End"),
        ]
        result = to_valhalla_route(fixture, wps)
        locs = result["trip"]["locations"]
        assert locs[0]["name"] == "Start"
        assert locs[1]["name"] == "Mid"
        assert locs[2]["name"] == "End"

    def test_non_ok_code_raises(self):
        with pytest.raises(ValueError, match="not Ok"):
            to_valhalla_route({"code": "NoRoute"}, [])


class TestToValhallaMatrix:
    def test_basic_matrix(self):
        fixture = _load("osrm_table_response.json")
        result = to_valhalla_matrix(fixture)

        assert "sources_to_targets" in result
        pairs = result["sources_to_targets"]
        # 3x3 = 9 pairs, minus the None (diagonal?) or all valid
        assert len(pairs) == 9
        for pair in pairs:
            assert "time" in pair
            assert "distance" in pair

    def test_non_ok_raises(self):
        with pytest.raises(ValueError, match="not Ok"):
            to_valhalla_matrix({"code": "NoTable"})


class TestToValhallaTrace:
    def test_basic_trace(self):
        fixture = _load("osrm_match_response.json")
        result = to_valhalla_trace(fixture)

        assert "trip" in result
        assert "confidence" in result
        assert result["confidence"] == 0.92
        trip = result["trip"]
        assert len(trip["legs"]) == 1

    def test_non_ok_raises(self):
        with pytest.raises(ValueError):
            to_valhalla_trace({"code": "NoMatch"})


class TestToValhallaLocate:
    def test_basic_locate(self):
        fixture = _load("osrm_nearest_response.json")
        result = to_valhalla_locate(fixture, -6.2255, 106.8228)

        assert "results" in result
        r = result["results"][0]
        assert r["name"] == "Jalan Sudirman"
        assert r["distance_m"] == 12.5
        assert r["input_lat"] == -6.2255
        assert r["input_lon"] == 106.8228


class TestPolyline6Codec:
    """Guard against the v0.2.0 step-concatenation bug.

    The bug: encoded polylines were string-concatenated across steps,
    producing wild jumps back toward (0,0). The fix decodes each step,
    drops the duplicated joining point, and re-encodes the leg.
    """

    def test_roundtrip_preserves_coords(self):
        from routing_plan.core.osrm_normalize import (
            _decode_polyline6, _encode_polyline6,
        )
        original = [(-7.7826, 110.3675), (-7.7929, 110.3656), (-7.8052, 110.3642)]
        encoded = _encode_polyline6(original)
        decoded = _decode_polyline6(encoded)
        assert len(decoded) == 3
        for (lat0, lon0), (lat1, lon1) in zip(original, decoded):
            assert abs(lat0 - lat1) < 1e-5
            assert abs(lon0 - lon1) < 1e-5

    def test_two_step_route_shape_stays_in_yogyakarta(self):
        """End-to-end: two OSRM steps whose decoded points are both in
        Yogyakarta should produce a leg shape whose decoded points are
        ALL in Yogyakarta (no Atlantic-ocean snap-back)."""
        from routing_plan.core.osrm_normalize import (
            _decode_polyline6, _encode_polyline6, to_valhalla_route,
        )
        # Build two synthetic steps that overlap on their joining point.
        step1_pts = [(-7.7826, 110.3675), (-7.7900, 110.3660)]
        step2_pts = [(-7.7900, 110.3660), (-7.8052, 110.3642)]
        osrm_resp = {
            "code": "Ok",
            "waypoints": [
                {"name": "A", "location": [110.3675, -7.7826]},
                {"name": "B", "location": [110.3642, -7.8052]},
            ],
            "routes": [{
                "distance": 3000.0, "duration": 600.0,
                "legs": [{
                    "distance": 3000.0, "duration": 600.0,
                    "steps": [
                        {"geometry": _encode_polyline6(step1_pts),
                         "name": "Jalan A", "distance": 1500.0, "duration": 300.0,
                         "maneuver": {"type": "depart", "modifier": None}},
                        {"geometry": _encode_polyline6(step2_pts),
                         "name": "Jalan B", "distance": 1500.0, "duration": 300.0,
                         "maneuver": {"type": "arrive", "modifier": None}},
                    ],
                }],
            }],
        }
        result = to_valhalla_route(osrm_resp, waypoints=[])
        leg_shape = result["trip"]["legs"][0]["shape"]
        pts = _decode_polyline6(leg_shape)

        # Expect 3 unique points (4 raw, minus 1 duplicate at the join).
        assert len(pts) == 3, f"expected 3 points after dedupe, got {len(pts)}: {pts}"
        # ALL points must stay in Yogyakarta (roughly -8 < lat < -7, 110 < lon < 111).
        for lat, lon in pts:
            assert -8.5 < lat < -7.0, f"lat {lat} drifted out of Yogyakarta"
            assert 109.5 < lon < 111.0, f"lon {lon} drifted out of Yogyakarta"

    def test_begin_shape_index_points_into_decoded_leg(self):
        """Maneuver begin_shape_index must be a point-index into the
        decoded leg polyline, not a maneuver counter."""
        from routing_plan.core.osrm_normalize import (
            _encode_polyline6, to_valhalla_route,
        )
        step1_pts = [(-7.7826, 110.3675), (-7.7900, 110.3660), (-7.7950, 110.3650)]
        step2_pts = [(-7.7950, 110.3650), (-7.8052, 110.3642)]
        osrm_resp = {
            "code": "Ok",
            "waypoints": [
                {"name": "A", "location": [110.3675, -7.7826]},
                {"name": "B", "location": [110.3642, -7.8052]},
            ],
            "routes": [{
                "distance": 0, "duration": 0,
                "legs": [{
                    "distance": 0, "duration": 0,
                    "steps": [
                        {"geometry": _encode_polyline6(step1_pts), "name": "A",
                         "distance": 0, "duration": 0,
                         "maneuver": {"type": "depart", "modifier": None}},
                        {"geometry": _encode_polyline6(step2_pts), "name": "B",
                         "distance": 0, "duration": 0,
                         "maneuver": {"type": "arrive", "modifier": None}},
                    ],
                }],
            }],
        }
        result = to_valhalla_route(osrm_resp, waypoints=[])
        maneuvers = result["trip"]["legs"][0]["maneuvers"]
        # First maneuver starts at point 0; second starts after step1's
        # 3 points (with no dedupe needed for the first step).
        assert maneuvers[0]["begin_shape_index"] == 0
        assert maneuvers[1]["begin_shape_index"] == 3

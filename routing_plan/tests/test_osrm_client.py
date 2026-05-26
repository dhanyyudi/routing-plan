"""Tests for OSRM client error classification and public interface."""

import json
import pytest
from routing_plan.core.osrm_client import OSRMClient, OSRMError, _classify_error
from routing_plan.core.engine import EngineCapabilityError


class TestOSRMError:
    @pytest.mark.parametrize(
        "code,expected_kind",
        [
            ("NoRoute", "no_route"),
            ("NoSegment", "out_of_coverage"),
            ("NoTrips", "out_of_coverage"),
            ("NoMatch", "out_of_coverage"),
            ("InvalidUrl", "invalid"),
            ("InvalidValue", "invalid"),
            ("TooBig", "invalid"),
        ],
    )
    def test_error_classification(self, code, expected_kind):
        body = json.dumps({"code": code, "message": "test"})
        err = _classify_error(200 if code == "Ok" else 400, body)
        assert err.kind == expected_kind
        assert err.code == code

    def test_network_error(self):
        err = _classify_error(500, "")
        assert err.kind == "network"

    def test_error_str(self):
        err = OSRMError("no_route", "NoRoute", "No route found")
        assert "NoRoute" in str(err)


class TestOSRMClientUnsupported:
    def test_unsupported_features_raise(self):
        client = OSRMClient(endpoint="http://test")
        with pytest.raises(EngineCapabilityError, match="isochrone"):
            client.isochrone()
        with pytest.raises(EngineCapabilityError, match="trace_attributes"):
            client.trace_attributes()
        with pytest.raises(EngineCapabilityError, match="expansion"):
            client.expansion()
        with pytest.raises(EngineCapabilityError, match="height"):
            client.height()

    def test_resolve_profile(self):
        assert OSRMClient._resolve_profile("auto") == "car"
        assert OSRMClient._resolve_profile("car") == "car"
        assert OSRMClient._resolve_profile("bicycle") == "bike"
        assert OSRMClient._resolve_profile("pedestrian") == "foot"
        assert OSRMClient._resolve_profile("truck") == "car"

    def test_waypoints_to_string(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [
            Waypoint(lat=52.5, lon=13.4, name="A"),
            Waypoint(lat=52.6, lon=13.5, name="B"),
        ]
        result = OSRMClient._waypoints_to_string(wps)
        assert result == "13.4,52.5;13.5,52.6"


class TestOSRMUrlConstruction:
    """Mock _do_get and assert the URL passed in matches the OSRM API."""

    def test_matrix_url_uses_indices_not_coordinates(self, monkeypatch):
        from routing_plan.core.waypoint_loader import Waypoint
        client = OSRMClient(endpoint="http://test")
        captured = {}

        def fake_get(self, url):
            captured["url"] = url
            return {"code": "Ok", "durations": [[0]], "distances": [[0]],
                    "sources": [], "destinations": []}

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        sources = [Waypoint(lat=52.5, lon=13.4, name="A")]
        targets = [Waypoint(lat=52.6, lon=13.5, name="B"),
                   Waypoint(lat=52.7, lon=13.6, name="C")]
        client.matrix(sources, targets)

        url = captured["url"]
        # all coordinates appear in the path
        assert "13.4,52.5;13.5,52.6;13.6,52.7" in url
        # sources= and destinations= are integer indices
        assert "sources=0" in url
        assert "destinations=1;2" in url
        # bug guard: destinations should NOT contain a comma (coordinates leaked)
        assert "destinations=13" not in url

    def test_route_url_uses_polyline6(self, monkeypatch):
        from routing_plan.core.waypoint_loader import Waypoint
        client = OSRMClient(endpoint="http://test")
        captured = {}

        def fake_get(self, url):
            captured["u"] = url
            return {"code": "Ok", "routes": [{"legs": []}], "waypoints": []}

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        client.route([Waypoint(lat=52.5, lon=13.4, name="A"),
                      Waypoint(lat=52.6, lon=13.5, name="B")])
        assert "geometries=polyline6" in captured["u"]
        assert "steps=true" in captured["u"]

    def test_trip_endpoint(self, monkeypatch):
        from routing_plan.core.waypoint_loader import Waypoint
        client = OSRMClient(endpoint="http://test")
        captured = {}

        def fake_get(self, url):
            captured["u"] = url
            return {"code": "Ok", "trips": [{"legs": []}], "waypoints": []}

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        client.optimized_route([Waypoint(lat=52.5, lon=13.4, name="A"),
                                Waypoint(lat=52.6, lon=13.5, name="B")])
        assert "/trip/v1/" in captured["u"]
        assert "source=first" in captured["u"]
        assert "destination=last" in captured["u"]

    def test_match_endpoint(self, monkeypatch):
        client = OSRMClient(endpoint="http://test")
        captured = {}

        def fake_get(self, url):
            captured["u"] = url
            return {"code": "Ok", "matchings": [{"legs": [], "confidence": 1.0}],
                    "tracepoints": []}

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        client.trace_route([{"lat": 52.5, "lon": 13.4}, {"lat": 52.6, "lon": 13.5}])
        assert "/match/v1/" in captured["u"]

    def test_nearest_endpoint(self, monkeypatch):
        client = OSRMClient(endpoint="http://test")
        captured = {}

        def fake_get(self, url):
            captured["u"] = url
            return {"code": "Ok", "waypoints": []}

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        client.locate(52.5, 13.4)
        assert "/nearest/v1/" in captured["u"]
        assert "13.4,52.5" in captured["u"]

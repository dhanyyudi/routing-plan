import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from routing_plan.core.valhalla_client import (
    decode_polyline6,
    ValhallaError,
    _classify_error,
    ValhallaClient,
    NO_ROUTE_CODES,
    OUT_OF_COVERAGE_CODES,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDecodePolyline6:
    def test_empty_string(self):
        assert decode_polyline6("") == []

    def test_single_point(self):
        coords = decode_polyline6("??")
        assert coords == [(0.0, 0.0)]

    def test_two_points(self):
        with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
            data = json.load(f)
        shape = data["trip"]["legs"][0]["shape"]
        coords = decode_polyline6(shape)
        assert len(coords) >= 2
        assert coords[0] != coords[1]

    def test_known_encoded(self):
        coords = decode_polyline6("??")
        assert len(coords) == 1
        assert coords[0] == pytest.approx((0.0, 0.0))

    def test_decoded_is_list_of_tuples(self):
        coords = decode_polyline6("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
        assert isinstance(coords, list)
        for c in coords:
            assert isinstance(c, tuple)
            assert len(c) == 2
            assert isinstance(c[0], float)
            assert isinstance(c[1], float)

    def test_mock_shape_decodes(self):
        with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
            data = json.load(f)
        shape = data["trip"]["legs"][0]["shape"]
        coords = decode_polyline6(shape)
        assert len(coords) > 10
        assert coords[0][0] == pytest.approx(-6.175514, rel=1e-5)
        assert coords[0][1] == pytest.approx(106.830053, rel=1e-5)
        for lat, lon in coords:
            assert -90 <= lat <= 90
            assert -180 <= lon <= 180


class TestClassifyError:
    def test_no_route_442(self):
        err = _classify_error(400, json.dumps({"error_code": 442, "error": "No path"}))
        assert err.kind == "no_route"
        assert err.code == 442

    def test_no_route_444(self):
        err = _classify_error(400, json.dumps({"error_code": 444, "error": "No path"}))
        assert err.kind == "no_route"

    def test_out_of_coverage_171(self):
        err = _classify_error(400, json.dumps({"error_code": 171, "error": "No edges"}))
        assert err.kind == "out_of_coverage"
        assert err.code == 171

    def test_out_of_coverage_170(self):
        err = _classify_error(400, json.dumps({"error_code": 170, "error": ""}))
        assert err.kind == "out_of_coverage"

    def test_out_of_coverage_154(self):
        err = _classify_error(400, json.dumps({"error_code": 154, "error": ""}))
        assert err.kind == "out_of_coverage"

    def test_invalid_other_code(self):
        err = _classify_error(400, json.dumps({"error_code": 999, "error": "WTF"}))
        assert err.kind == "invalid"
        assert err.code == 999

    def test_invalid_malformed_body(self):
        err = _classify_error(500, "not json")
        assert err.kind == "invalid"
        assert err.code == 500

    def test_valid_response(self):
        with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
            data = json.load(f)
        assert "trip" in data
        assert data["trip"]["status"] == 0


class TestValhallaError:
    def test_str_representation(self):
        err = ValhallaError("no_route", 442, "No path found", {"raw": "data"})
        s = str(err)
        assert "no_route" in s
        assert "No path found" in s
        assert "442" in s

    def test_is_exception(self):
        err = ValhallaError("network", -1, "timeout")
        assert isinstance(err, Exception)

    def test_raw_optional(self):
        err = ValhallaError("invalid", 500, "server error")
        assert err.raw is None


class TestValhallaClient:
    def test_init_defaults(self):
        client = ValhallaClient()
        assert client.endpoint == "https://valhalla.dhanypedia.it.com"
        assert client.timeout == 60

    def test_init_custom(self):
        client = ValhallaClient("http://localhost:8002", timeout=30)
        assert client.endpoint == "http://localhost:8002"
        assert client.timeout == 30

    def test_trailing_slash_removed(self):
        client = ValhallaClient("http://localhost:8002/")
        assert client.endpoint == "http://localhost:8002"

    def test_invalid_costing_mode(self):
        client = ValhallaClient()
        with pytest.raises(ValueError, match="Invalid costing mode"):
            client._build_payload([], "helicopter", None, None, 0, None, None)

    def test_build_payload_minimal(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [Waypoint(lat=-6.175, lon=106.827, name="Monas"),
               Waypoint(lat=-6.186, lon=106.834, name="Gambir")]
        client = ValhallaClient()
        payload = client._build_payload(wps, "auto", None, None, 0, None, None)
        assert payload["costing"] == "auto"
        assert len(payload["locations"]) == 2
        assert payload["locations"][0]["lat"] == -6.175
        assert payload["locations"][0]["lon"] == 106.827
        assert payload["locations"][0]["name"] == "Monas"
        assert payload["locations"][0]["type"] == "break"
        assert payload["id"] == "routing-plan-qgis"
        assert "directions_options" in payload
        assert "alternates" not in payload

    def test_build_payload_with_options(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [Waypoint(lat=-6.175, lon=106.827), Waypoint(lat=-6.186, lon=106.834)]
        client = ValhallaClient()
        payload = client._build_payload(
            wps, "pedestrian",
            costing_options={"pedestrian": {"walking_speed": 5.1}},
            directions_options={"units": "miles", "language": "en"},
            alternates=2,
            date_time={"type": 1, "value": "2026-05-23T10:00"},
            exclude_polygons=[[[106.8, -6.2], [106.9, -6.2], [106.9, -6.1]]],
        )
        assert payload["alternates"] == 2
        assert "date_time" in payload
        assert "exclude_polygons" in payload
        assert payload["costing_options"] == {"pedestrian": {"walking_speed": 5.1}}

    def test_build_payload_waypoint_without_name(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [Waypoint(lat=-6.175, lon=106.827), Waypoint(lat=-6.186, lon=106.834)]
        client = ValhallaClient()
        payload = client._build_payload(wps, "auto", None, None, 0, None, None)
        assert "name" not in payload["locations"][0]

    def test_route_returns_parsed_json(self):
        from routing_plan.core.waypoint_loader import Waypoint
        with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
            mock_data = json.load(f)
        wps = [Waypoint(lat=-6.175, lon=106.827, name="Monas"),
               Waypoint(lat=-6.186, lon=106.834, name="Gambir")]
        client = ValhallaClient()
        with patch.object(client, '_do_request', return_value=mock_data) as mock_req:
            result = client.route(wps, costing="auto")
            mock_req.assert_called_once()
            assert result == mock_data
            assert result["trip"]["status"] == 0

    def test_optimized_route_uses_correct_path(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [Waypoint(lat=-6.175, lon=106.827), Waypoint(lat=-6.186, lon=106.834)]
        client = ValhallaClient()
        with patch.object(client, '_do_request', return_value={"trip": {"status": 0}}) as mock_req:
            client.optimized_route(wps, costing="auto")
            mock_req.assert_called_once()
            args = mock_req.call_args[0]
            assert args[0] == "/optimized_route"

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

with open(FIXTURES_DIR / "valhalla_response_mock.json") as f:
    MOCK_RESPONSE = json.load(f)

from routing_plan.core.exporter import (  # noqa: E402
    export_html,
    export_geojson,
    export_kml,
    _build_geojson,
    _get_bounds,
    _build_maneuver_rows_html,
)


class TestBuildGeoJson:
    def test_returns_feature_collection(self):
        data = _build_geojson(MOCK_RESPONSE)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    def test_has_linestring_features(self):
        data = _build_geojson(MOCK_RESPONSE)
        lines = [f for f in data["features"] if f["geometry"]["type"] == "LineString"]
        assert len(lines) == 1
        assert lines[0]["properties"]["leg_index"] == 0
        assert lines[0]["properties"]["from"] == "Monas"
        assert lines[0]["properties"]["to"] == "Stasiun Gambir"

    def test_has_point_features(self):
        data = _build_geojson(MOCK_RESPONSE)
        points = [f for f in data["features"] if f["geometry"]["type"] == "Point"]
        assert len(points) >= 4
        for pt in points:
            assert "instruction" in pt["properties"]
            assert "maneuver_type" in pt["properties"]

    def test_linestring_coordinates_are_lon_lat(self):
        data = _build_geojson(MOCK_RESPONSE)
        line = [f for f in data["features"] if f["geometry"]["type"] == "LineString"][0]
        coords = line["geometry"]["coordinates"]
        assert len(coords) > 10
        for c in coords:
            assert len(c) == 2
            assert -180 <= c[0] <= 180
            assert -90 <= c[1] <= 90


class TestGetBounds:
    def test_returns_valid_bounds(self):
        bounds = _get_bounds(MOCK_RESPONSE)
        parsed = json.loads(bounds)
        assert len(parsed) == 2
        assert len(parsed[0]) == 2
        assert len(parsed[1]) == 2
        assert parsed[0][0] < parsed[1][0]


class TestManeuverRowsHtml:
    def test_returns_html_strings(self):
        rows = [
            {"icon": "↑", "instruction": "Drive south.", "distance": "40 m", "street": ""},
            {"icon": "↰", "instruction": "Turn left.", "distance": "170 m", "street": "Jalan Medan Merdeka Selatan"},
        ]
        html = _build_maneuver_rows_html(rows)
        assert "maneuver-item" in html
        assert "Drive south" in html
        assert "Turn left" in html
        assert "Jalan Medan Merdeka Selatan" in html


class TestExportHtml:
    def test_creates_html_file(self):
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
            tmp = f.name
        try:
            result = export_html(MOCK_RESPONSE, tmp)
            assert os.path.exists(result)
            content = open(result).read()
            assert "<!DOCTYPE html>" in content
            assert "Monas" in content
            assert "leaflet" in content.lower()
        finally:
            os.unlink(tmp)

    def test_contains_geojson_data(self):
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
            tmp = f.name
        try:
            export_html(MOCK_RESPONSE, tmp)
            content = open(tmp).read()
            assert "FeatureCollection" in content
            assert '"LineString"' in content
        finally:
            os.unlink(tmp)


class TestExportGeoJson:
    def test_creates_geojson_file(self):
        with tempfile.NamedTemporaryFile(suffix=".geojson", mode="w", delete=False) as f:
            tmp = f.name
        try:
            result = export_geojson(MOCK_RESPONSE, tmp)
            assert os.path.exists(result)
            data = json.load(open(result))
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) >= 5
        finally:
            os.unlink(tmp)


class TestExportKml:
    def test_creates_kml_file(self):
        with tempfile.NamedTemporaryFile(suffix=".kml", mode="w", delete=False) as f:
            tmp = f.name
        try:
            result = export_kml(MOCK_RESPONSE, tmp)
            assert os.path.exists(result)
            content = open(result).read()
            assert '<?xml version="1.0"' in content
            assert "<kml" in content
            assert "<Document>" in content
            assert "<Placemark>" in content
            assert "<LineString>" in content
        finally:
            os.unlink(tmp)

    def test_kml_has_leg_and_maneuver_placemarks(self):
        with tempfile.NamedTemporaryFile(suffix=".kml", mode="w", delete=False) as f:
            tmp = f.name
        try:
            export_kml(MOCK_RESPONSE, tmp)
            content = open(tmp).read()
            assert "Leg 1: Monas" in content
            assert "Maneuver 0_0" in content
        finally:
            os.unlink(tmp)

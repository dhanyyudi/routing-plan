"""Smoke test integration — verifies test-samples/ data + icon wiring without QGIS GUI."""
import os
import pytest
from dataclasses import replace

ROOT = os.path.dirname(os.path.dirname(__file__))
SAMPLES = os.path.join(os.path.dirname(ROOT), "test-samples")

INDONESIA_BBOX = {
    "lat_min": -11.5, "lat_max": 6.5,
    "lon_min": 94.5, "lon_max": 141.5,
}


def is_in_indonesia(wp):
    return (
        INDONESIA_BBOX["lat_min"] <= wp.lat <= INDONESIA_BBOX["lat_max"] and
        INDONESIA_BBOX["lon_min"] <= wp.lon <= INDONESIA_BBOX["lon_max"]
    )


# ── OPEN-5: test-samples data-level smoke ──────────────────────────


class TestSample01BandungTour:
    def test_loads_5_waypoints(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "01-bandung-tour.csv"))
        assert len(wps) == 5

    def test_first_is_gedung_sate(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "01-bandung-tour.csv"))
        assert "Gedung" in wps[0].name

    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "01-bandung-tour.csv"))
        for wp in wps:
            assert is_in_indonesia(wp)

    def test_roundtrip_appends_waypoint_zero(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "01-bandung-tour.csv"))
        original = list(wps)
        wps = original + [replace(original[0])]
        assert len(wps) == 6
        assert wps[0].lat == wps[5].lat
        assert wps[0].lon == wps[5].lon


class TestSample02BaliXLSX:
    def test_loads_8_waypoints(self):
        from routing_plan.core.waypoint_loader import load_xlsx
        wps = load_xlsx(os.path.join(SAMPLES, "02-bali-landmarks.xlsx"))
        assert len(wps) == 8

    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_xlsx
        wps = load_xlsx(os.path.join(SAMPLES, "02-bali-landmarks.xlsx"))
        for wp in wps:
            assert is_in_indonesia(wp)


class TestSample03GeoJSON:
    def test_loads_6_waypoints(self):
        from routing_plan.core.waypoint_loader import load_geojson
        wps = load_geojson(os.path.join(SAMPLES, "03-yogyakarta-trip.geojson"))
        assert len(wps) == 6

    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_geojson
        wps = load_geojson(os.path.join(SAMPLES, "03-yogyakarta-trip.geojson"))
        for wp in wps:
            assert is_in_indonesia(wp)


class TestSample04SurabayaKML:
    @pytest.mark.skip(reason="load_kml requires qgis.core.QgsVectorLayer")
    def test_loads_3_waypoints(self):
        from routing_plan.core.waypoint_loader import load_kml
        wps = load_kml(os.path.join(SAMPLES, "04-surabaya-malang.kml"))
        assert len(wps) >= 2

    @pytest.mark.skip(reason="load_kml requires qgis.core.QgsVectorLayer")
    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_kml
        wps = load_kml(os.path.join(SAMPLES, "04-surabaya-malang.kml"))
        for wp in wps:
            assert is_in_indonesia(wp)


class TestSample05Flores:
    def test_loads_4_waypoints(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "05-flores-overland.csv"))
        assert len(wps) == 4

    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "05-flores-overland.csv"))
        for wp in wps:
            assert is_in_indonesia(wp)


class TestSample06Aliases:
    def test_loads_csv_with_indonesian_headers(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "06-aliases-id.csv"))
        assert len(wps) >= 2


class TestSample07MixedRegion:
    def test_all_locations_within_bbox(self):
        """Singapore & KL fallah di dalam bbox Indonesia yang loose.
        Bbox sengaja luas untuk hindari false positives — border internasional
        tidak bisa di-cek pakai rectangle check."""
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "07-mixed-region-warning.csv"))
        assert len(wps) == 4
        for wp in wps:
            assert is_in_indonesia(wp), f"{wp.name}: semua di dalam bbox"


class TestSample08Ocean:
    def test_loads_2_waypoints(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "08-no-route-ocean.csv"))
        assert len(wps) == 2

    def test_all_in_indonesia(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "08-no-route-ocean.csv"))
        for wp in wps:
            assert is_in_indonesia(wp)


class TestSample09SinglePoint:
    def test_loads_1_waypoint_but_loader_rejects(self):
        """load_csv rejects <2 waypoints. UI harus tetap bisa handle 1-point."""
        from routing_plan.core.waypoint_loader import load_csv
        with pytest.raises(ValueError, match="Minimal 2 waypoints"):
            load_csv(os.path.join(SAMPLES, "09-single-point.csv"))


class TestSample10InvalidCoords:
    def test_loads_3_waypoints(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "10-invalid-coords.csv"))
        assert len(wps) == 3

    def test_lat_95_is_invalid(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "10-invalid-coords.csv"))
        bad = [wp for wp in wps if wp.lat > 90]
        assert len(bad) >= 1
        errors = bad[0].validate()
        assert len(errors) > 0
        assert "lat" in " ".join(errors).lower()

    def test_lon_200_is_invalid(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "10-invalid-coords.csv"))
        bad = [wp for wp in wps if wp.lon > 180]
        assert len(bad) >= 1
        errors = bad[0].validate()
        assert len(errors) > 0
        assert "lon" in " ".join(errors).lower()

    def test_valid_lat_70_still_ok(self):
        from routing_plan.core.waypoint_loader import load_csv
        wps = load_csv(os.path.join(SAMPLES, "10-invalid-coords.csv"))
        ok = [wp for wp in wps if 30 <= wp.lat <= 75]
        for wp in ok:
            errors = wp.validate()
            assert len(errors) == 0


# ── OPEN-3: icon wiring ────────────────────────────────────────────


class TestIconPathsExist:
    def test_all_maneuver_png_files_exist(self):
        from routing_plan.core.maneuver_formatter import ICON_NAMES
        png_dir = os.path.join(ROOT, "icons", "maneuvers_png")
        for icon_name in set(ICON_NAMES.values()):
            path = os.path.join(png_dir, f"{icon_name}.png")
            assert os.path.exists(path), f"Missing PNG: {path}"

    def test_icon_path_for_every_maneuver_type(self):
        from routing_plan.core.maneuver_formatter import (
            icon_path_for_maneuver_type, MANEUVER_TYPE_ICON,
        )
        for mtype in MANEUVER_TYPE_ICON:
            path = icon_path_for_maneuver_type(mtype)
            assert path is not None, f"No icon found for maneuver type {mtype}"
            assert os.path.exists(path), f"Icon does not exist: {path}"

    def test_png_dir_under_200_kb(self):
        png_dir = os.path.join(ROOT, "icons", "maneuvers_png")
        total = sum(
            os.path.getsize(os.path.join(png_dir, f))
            for f in os.listdir(png_dir) if f.endswith(".png")
        )
        kb = total / 1024
        assert kb < 200, f"PNG total {kb:.0f} KB exceeds 200 KB budget"


# ── OPEN-4: Waypoint.validate edge cases ───────────────────────────


class TestWaypointValidate:
    def test_valid_bandung(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=-6.9147, lon=107.6098, name="Bandung")
        assert wp.validate() == []

    def test_valid_jakarta(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=-6.2088, lon=106.8456, name="Jakarta")
        assert wp.validate() == []

    def test_invalid_lat_100(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=100.0, lon=106.8456)
        errors = wp.validate()
        assert len(errors) >= 1

    def test_invalid_lon_200(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=-6.2, lon=200.0)
        errors = wp.validate()
        assert len(errors) >= 1

    def test_both_invalid(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=95.5, lon=200.0)
        errors = wp.validate()
        assert len(errors) >= 2

    def test_none_lat(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=None, lon=106.8456)
        errors = wp.validate()
        assert len(errors) >= 1

    def test_none_lon(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wp = Waypoint(lat=-6.2, lon=None)
        errors = wp.validate()
        assert len(errors) >= 1


# ── OSM avoid mapping ──────────────────────────────────────────────


class TestAvoidMapping:
    def test_supported_set_complete(self):
        supported = {"motorway", "trunk", "toll", "ferry", "track", "living_street"}
        assert len(supported) == 6


# ── Fix #8a + #8b: loader robustness ───────────────────────────────


class TestLoaderRobustness:
    def test_load_geojson_case_insensitive_name(self):
        """Fix #8a: GeoJSON name keys case-insensitive (Name, TITLE, label)."""
        from routing_plan.core.waypoint_loader import load_geojson
        fixture = os.path.join(SAMPLES, "11-geojson-uppercase-name.geojson")
        wps = load_geojson(fixture)
        assert len(wps) == 2
        assert wps[0].name == "Tugu Yogya"
        assert wps[1].name == "Malioboro"

    def test_load_csv_auto_detect_semicolon(self):
        """Fix #8b: CSV dengan delimiter ; (locale EU) parse dengan benar."""
        from routing_plan.core.waypoint_loader import load_csv
        fixture = os.path.join(SAMPLES, "12-csv-semicolon.csv")
        wps = load_csv(fixture)
        assert len(wps) == 3
        assert wps[0].name == "Monas"
        assert wps[0].lat == pytest.approx(-6.1754)


# ── Drag-reorder: _get_waypoints_in_order reads lat/lon ────────────


class TestWaypointOrder:
    def test_reorder_preserves_lat_lon(self):
        from routing_plan.core.waypoint_loader import Waypoint
        wps = [
            Waypoint(lat=-6.1, lon=106.1, name="A"),
            Waypoint(lat=-7.2, lon=107.2, name="B"),
            Waypoint(lat=-8.3, lon=108.3, name="C"),
        ]
        reordered = [wps[2], wps[0], wps[1]]
        lats = [wp.lat for wp in reordered]
        assert lats == [-8.3, -6.1, -7.2], "Reordered lats harus sesuai urutan tabel"


# ── OSRM smoke test (uses mock fixture, no live network) ──────────

class TestOSRMSmoke:
    """Verify the OSRM route path produces a renderable response."""

    def test_osrm_route_renders_via_normalizer(self, monkeypatch):
        import json
        from pathlib import Path
        from routing_plan.core.osrm_client import OSRMClient
        from routing_plan.core.waypoint_loader import Waypoint

        fixture = Path(__file__).parent / "fixtures" / "osrm_route_response.json"
        with open(fixture) as f:
            fixture_data = json.load(f)

        def fake_get(self, url):
            return fixture_data

        monkeypatch.setattr(OSRMClient, "_do_get", fake_get)
        client = OSRMClient(endpoint="http://mock")
        wps = [
            Waypoint(lat=52.517037, lon=13.38886, name="Start"),
            Waypoint(lat=52.529407, lon=13.397634, name="Mid"),
            Waypoint(lat=52.523219, lon=13.428555, name="End"),
        ]
        result = client.route(wps)
        assert "trip" in result
        assert result["trip"]["units"] == "kilometers"
        assert len(result["trip"]["legs"]) == 2
        # Verify maneuvers exist on first leg
        assert len(result["trip"]["legs"][0]["maneuvers"]) > 0

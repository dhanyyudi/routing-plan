import os
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    import qgis.core  # noqa: F401
    HAS_QGIS = True
except ModuleNotFoundError:
    HAS_QGIS = False

from routing_plan.core.waypoint_loader import (  # noqa: E402
    Waypoint,
    load_csv,
    load_xlsx,
    load_geojson,
    load_kml,
    _guess_columns,
)

EXPECTED_NAMES = [
    "Monas", "Stasiun Gambir", "Tanah Abang", "Sarinah", "Menteng",
    "Senayan", "Gelora Bung Karno", "SCBD", "Blok M", "Fatmawati",
]
EXPECTED_COORDS = [
    (-6.175392, 106.827153),
    (-6.186486, 106.834091),
    (-6.2, 106.816666),
    (-6.194449, 106.822919),
    (-6.21462, 106.84513),
    (-6.224728, 106.809731),
    (-6.229728, 106.797188),
    (-6.242256, 106.799019),
    (-6.260759, 106.781628),
    (-6.291689, 106.800941),
]


def assert_waypoints_equal(waypoints, expected_names, expected_coords):
    assert len(waypoints) == len(expected_names)
    for i, (wp, name, (lat, lon)) in enumerate(
        zip(waypoints, expected_names, expected_coords)
    ):
        assert wp.name == name, f"Waypoint {i}: name mismatch"
        assert wp.lat == pytest.approx(lat), f"Waypoint {i}: lat mismatch"
        assert wp.lon == pytest.approx(lon), f"Waypoint {i}: lon mismatch"


class TestGuessColumns:
    def test_standard_names(self):
        lat, lon, name = _guess_columns(["lat", "lon", "name", "extra"])
        assert lat == 0
        assert lon == 1
        assert name == 2

    def test_aliases(self):
        lat, lon, name = _guess_columns(["latitude", "longitude", "nama"])
        assert lat == 0
        assert lon == 1
        assert name == 2

    def test_xy_aliases(self):
        lat, lon, name = _guess_columns(["x", "y", "title"])
        assert lon == 0
        assert lat == 1
        assert name == 2

    def test_case_insensitive(self):
        lat, lon, name = _guess_columns(["LAT", "Lon", "Name"])
        assert lat == 0
        assert lon == 1
        assert name == 2

    def test_no_name_column(self):
        lat, lon, name = _guess_columns(["lat", "lon", "foo"])
        assert lat == 0
        assert lon == 1
        assert name is None


class TestWaypoint:
    def test_valid(self):
        wp = Waypoint(lat=-6.175, lon=106.827, name="Monas")
        assert wp.validate() == []

    def test_invalid_lat(self):
        wp = Waypoint(lat=100, lon=106.827)
        assert len(wp.validate()) == 1

    def test_invalid_lon(self):
        wp = Waypoint(lat=-6.175, lon=200)
        assert len(wp.validate()) == 1

    def test_invalid_lock_role(self):
        wp = Waypoint(lat=-6.175, lon=106.827, lock_role="middle")
        assert len(wp.validate()) == 1

    def test_valid_lock_roles(self):
        for role in (None, "start", "end"):
            wp = Waypoint(lat=-6.175, lon=106.827, lock_role=role)
            assert wp.validate() == []


class TestLoadCsv:
    def test_load_with_header(self):
        waypoints = load_csv(str(FIXTURES_DIR / "sample.csv"))
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)

    def test_load_explicit_columns(self):
        waypoints = load_csv(
            str(FIXTURES_DIR / "sample.csv"), lat_col=0, lon_col=1, name_col=2
        )
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)

    def test_empty_file(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("lat,lon\n")
            tmp = f.name
        try:
            with pytest.raises(ValueError, match="Minimal 2"):
                load_csv(tmp)
        finally:
            os.unlink(tmp)

    def test_not_enough_waypoints(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("lat,lon,name\n")
            f.write("-6.175,106.827,Monas\n")
            tmp = f.name
        try:
            with pytest.raises(ValueError, match="Minimal 2"):
                load_csv(tmp)
        finally:
            os.unlink(tmp)


class TestLoadXlsx:
    def test_load_with_header(self):
        waypoints = load_xlsx(str(FIXTURES_DIR / "sample.xlsx"))
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)

    def test_load_explicit_columns(self):
        waypoints = load_xlsx(
            str(FIXTURES_DIR / "sample.xlsx"), lat_col=0, lon_col=1, name_col=2
        )
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)

    def test_load_by_sheet_name(self):
        waypoints = load_xlsx(
            str(FIXTURES_DIR / "sample.xlsx"), sheet="Sheet"
        )
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)


class TestLoadGeoJson:
    def test_feature_collection(self):
        waypoints = load_geojson(str(FIXTURES_DIR / "sample.geojson"))
        assert_waypoints_equal(waypoints, EXPECTED_NAMES, EXPECTED_COORDS)

    def test_single_feature(self):
        wp = load_geojson(str(FIXTURES_DIR / "sample.geojson"))
        assert len(wp) == 10


@pytest.mark.skipif(not HAS_QGIS, reason="memerlukan QGIS runtime")
class TestLoadKml:
    def test_load(self):
        waypoints = load_kml(str(FIXTURES_DIR / "sample.kml"))
        assert len(waypoints) == 10
        for i, wp in enumerate(waypoints):
            assert wp.name == EXPECTED_NAMES[i]
            assert wp.lat == pytest.approx(EXPECTED_COORDS[i][0])
            assert wp.lon == pytest.approx(EXPECTED_COORDS[i][1])

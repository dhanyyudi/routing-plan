import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from routing_plan.core.maneuver_formatter import (  # noqa: E402
    format_distance,
    format_duration,
    format_total_summary,
    icon_for_maneuver_type,
    unicode_for_maneuver_type,
    MANEUVER_TYPE_ICON,
    ICON_NAMES,
)


class TestFormatDistance:
    def test_zero(self):
        assert format_distance(0) == "0 m"

    def test_meters(self):
        assert format_distance(5) == "5 m"
        assert format_distance(190) == "190 m"
        assert format_distance(999) == "999 m"

    def test_one_km(self):
        assert format_distance(1000) == "1,0 km"
        assert format_distance(4100) == "4,1 km"
        assert format_distance(9999) == "10,0 km"

    def test_large_km(self):
        assert format_distance(10500) == "10 km"
        assert format_distance(1200000) == "1.200 km"

    def test_none(self):
        assert format_distance(None) == ""

    def test_negative(self):
        assert format_distance(-1) == ""


class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(0) == "0 detik"
        assert format_duration(30) == "30 detik"
        assert format_duration(59) == "59 detik"

    def test_minutes(self):
        assert format_duration(60) == "1 menit"
        assert format_duration(420) == "7 menit"
        assert format_duration(3599) == "59 menit"

    def test_hours(self):
        assert format_duration(3600) == "1 jam"
        assert format_duration(7200) == "2 jam"

    def test_hours_minutes(self):
        assert format_duration(3660) == "1 j 1 m"
        assert format_duration(6304) == "1 j 45 m"

    def test_none(self):
        assert format_duration(None) == ""

    def test_negative(self):
        assert format_duration(-1) == ""


class TestFormatTotalSummary:
    def test_km_units(self):
        response = {
            "trip": {
                "summary": {"length": 43.44, "time": 6304},
                "units": "kilometers",
            }
        }
        result = format_total_summary(response)
        assert result["distance"] == "43 km"
        assert result["duration"] == "1 j 45 m"
        assert result["length_km"] == 43.44
        assert result["time_min"] == pytest.approx(105.1, rel=0.01)

    def test_miles_units(self):
        response = {
            "trip": {
                "summary": {"length": 10.0, "time": 1800},
                "units": "miles",
            }
        }
        result = format_total_summary(response)
        assert result["length_km"] == 10.0


class TestIconMapping:
    def test_known_types(self):
        assert icon_for_maneuver_type(1) == "maneuver_depart"
        assert icon_for_maneuver_type(4) == "maneuver_arrive"
        assert icon_for_maneuver_type(11) == "maneuver_turn_right"
        assert icon_for_maneuver_type(16) == "maneuver_turn_left"
        assert icon_for_maneuver_type(14) == "maneuver_uturn_left"
        assert icon_for_maneuver_type(13) == "maneuver_uturn_right"
        assert icon_for_maneuver_type(26) == "maneuver_roundabout"
        assert icon_for_maneuver_type(27) == "maneuver_roundabout"
        assert icon_for_maneuver_type(21) == "maneuver_ferry"
        assert icon_for_maneuver_type(23) == "maneuver_merge"

    def test_unknown_type_fallback(self):
        assert icon_for_maneuver_type(999) == "maneuver_straight"
        assert icon_for_maneuver_type(-1) == "maneuver_straight"

    def test_all_defined_types_have_icon(self):
        for mtype, icon_key in MANEUVER_TYPE_ICON.items():
            assert icon_key in ICON_NAMES, f"Missing icon name for {icon_key} (type {mtype})"

    def test_unicode_known(self):
        assert len(unicode_for_maneuver_type(11)) > 0
        assert len(unicode_for_maneuver_type(4)) > 0

    def test_unicode_fallback(self):
        assert unicode_for_maneuver_type(999) == "⬆"

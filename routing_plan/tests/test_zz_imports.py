"""Smoke test: import every top-level module to catch ImportError early.

Bug history:
- 2026-05-23 audit-3: directions_dock.py had wrong relative import path
  (`.maneuver_formatter` instead of `..core.maneuver_formatter`).
  All pytest tests passed green, but plugin crashed on Compute Route.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_import_plugin():
    import routing_plan.plugin  # noqa: F401


def test_import_core():
    import routing_plan.core.core  # noqa: F401


def test_import_route_task():
    import routing_plan.core.route_task  # noqa: F401


def test_import_valhalla_client():
    import routing_plan.core.valhalla_client  # noqa: F401


def test_import_waypoint_loader():
    import routing_plan.core.waypoint_loader  # noqa: F401


def test_import_route_renderer():
    import routing_plan.core.route_renderer  # noqa: F401


def test_import_maneuver_formatter():
    import routing_plan.core.maneuver_formatter  # noqa: F401


def test_import_exporter():
    import routing_plan.core.exporter  # noqa: F401


def test_import_settings():
    import routing_plan.core.settings  # noqa: F401


def test_import_engine():
    import routing_plan.core.engine  # noqa: F401


def test_import_maneuver_mapper():
    import routing_plan.core.maneuver_mapper  # noqa: F401


def test_import_osrm_client():
    """Smoke: OSRMClient import succeeds without QGIS."""
    import routing_plan.core.osrm_client  # noqa: F401


def test_import_osrm_normalize():
    import routing_plan.core.osrm_normalize  # noqa: F401


def test_import_isochrone_renderer():
    import routing_plan.core.isochrone_renderer  # noqa: F401


def test_import_matrix_renderer():
    import routing_plan.core.matrix_renderer  # noqa: F401


def test_import_match_renderer():
    import routing_plan.core.match_renderer  # noqa: F401


def test_import_expansion_renderer():
    import routing_plan.core.expansion_renderer  # noqa: F401


def test_import_elevation_renderer():
    import routing_plan.core.elevation_renderer  # noqa: F401


def test_import_locate_renderer():
    import routing_plan.core.locate_renderer  # noqa: F401


def test_import_main_dialog():
    import routing_plan.ui.main_dialog  # noqa: F401


def test_import_directions_dock():
    """REGRESSION GUARD: caught audit-3 Fix #1 ModuleNotFoundError."""
    import routing_plan.ui.directions_dock  # noqa: F401


def test_import_settings_dialog():
    import routing_plan.ui.settings_dialog  # noqa: F401


def test_import_isochrone_dialog():
    import routing_plan.ui.isochrone_dialog  # noqa: F401


def test_import_matrix_dialog():
    import routing_plan.ui.matrix_dialog  # noqa: F401


def test_import_match_dialog():
    import routing_plan.ui.match_dialog  # noqa: F401


def test_import_expansion_dialog():
    import routing_plan.ui.expansion_dialog  # noqa: F401


def test_import_elevation_dialog():
    import routing_plan.ui.elevation_dialog  # noqa: F401


def test_import_locate_dialog():
    import routing_plan.ui.locate_dialog  # noqa: F401


def test_import_i18n():
    import routing_plan.i18n  # noqa: F401

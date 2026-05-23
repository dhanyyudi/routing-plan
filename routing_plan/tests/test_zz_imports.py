"""Smoke test: import every top-level module to catch ImportError early.

Bug history:
- 2026-05-23 audit-3: directions_dock.py had wrong relative import path
  (`.maneuver_formatter` instead of `..core.maneuver_formatter`).
  All pytest tests passed green, but plugin crashed on Compute Route.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="module", autouse=True)
def mock_qgis_modules():
    """Mock qgis so plain pytest can import plugin modules."""
    old_modules = {}
    for mod_name in ["qgis", "qgis.core", "qgis.gui", "qgis.PyQt",
                     "qgis.PyQt.QtCore", "qgis.PyQt.QtGui",
                     "qgis.PyQt.QtWidgets", "qgis.PyQt.QtNetwork"]:
        old_modules[mod_name] = sys.modules.get(mod_name)

    qgis = MagicMock()
    qgis.core = MagicMock()
    qgis.gui = MagicMock()
    qgis.PyQt = MagicMock()
    qgis.PyQt.QtCore = MagicMock()
    qgis.PyQt.QtGui = MagicMock()
    qgis.PyQt.QtWidgets = MagicMock()
    qgis.PyQt.QtNetwork = MagicMock()
    sys.modules["qgis"] = qgis
    sys.modules["qgis.core"] = qgis.core
    sys.modules["qgis.gui"] = qgis.gui
    sys.modules["qgis.PyQt"] = qgis.PyQt
    sys.modules["qgis.PyQt.QtCore"] = qgis.PyQt.QtCore
    sys.modules["qgis.PyQt.QtGui"] = qgis.PyQt.QtGui
    sys.modules["qgis.PyQt.QtWidgets"] = qgis.PyQt.QtWidgets
    sys.modules["qgis.PyQt.QtNetwork"] = qgis.PyQt.QtNetwork
    yield
    for mod_name, old_mod in old_modules.items():
        if old_mod is not None:
            sys.modules[mod_name] = old_mod
        elif mod_name in sys.modules:
            del sys.modules[mod_name]


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

def test_import_main_dialog():
    import routing_plan.ui.main_dialog  # noqa: F401

def test_import_directions_dock():
    """REGRESSION GUARD: caught audit-3 Fix #1 ModuleNotFoundError."""
    import routing_plan.ui.directions_dock  # noqa: F401

def test_import_settings_dialog():
    import routing_plan.ui.settings_dialog  # noqa: F401

def test_import_i18n():
    import routing_plan.i18n  # noqa: F401

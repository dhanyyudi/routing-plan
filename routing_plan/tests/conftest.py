"""Shared test fixtures for the routing_plan test suite.

Provides mock_qgis_modules so any test file can import renderer / dialog
modules without a QGIS installation.
"""

import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="module", autouse=True)
def mock_qgis_modules():
    """Mock qgis modules globally so plain pytest can import plugin modules."""
    old_modules = {}
    for mod_name in [
        "qgis", "qgis.core", "qgis.gui", "qgis.PyQt",
        "qgis.PyQt.QtCore", "qgis.PyQt.QtGui",
        "qgis.PyQt.QtWidgets", "qgis.PyQt.QtNetwork",
    ]:
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

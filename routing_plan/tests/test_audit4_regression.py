"""Regression guards for audit-4 BLOCKERS.

BLOCKER-A: CRS-aware canvas zoom (layerExtentToOutputExtent)
BLOCKER-B: build_stops_layer called in _on_route_done
FOLLOWUP: PyQt6 scoped enum for QgsPalLayerSettings.Placement
"""
import inspect
import os

from routing_plan.core import core, route_renderer


class TestBlockerA:
    """Canvas zoom must be CRS-aware, not raw setExtent(layer.extent())."""

    def test_extent_uses_layer_extent_to_output(self):
        src = inspect.getsource(core.ValhallaNavigatorCore._on_route_done)
        assert "layerExtentToOutputExtent" in src, (
            "BLOCKER-A regression: _on_route_done must use "
            "layerExtentToOutputExtent() for CRS-aware canvas zoom"
        )


class TestBlockerB:
    """build_stops_layer must be imported and called in _on_route_done."""

    def test_build_stops_layer_imported(self):
        src = inspect.getsource(core.ValhallaNavigatorCore._on_route_done)
        assert "build_stops_layer" in src, (
            "BLOCKER-B regression: _on_route_done must call build_stops_layer"
        )


class TestFollowupScopedEnum:
    """PyQt6 scoped enum must be used for QgsPalLayerSettings.Placement."""

    def test_placement_uses_scoped_enum(self):
        src = inspect.getsource(route_renderer._apply_stops_style)
        assert "QgsPalLayerSettings.Placement.OverPoint" in src, (
            "FOLLOWUP regression: must use scoped enum "
            "QgsPalLayerSettings.Placement.OverPoint"
        )

    def test_no_flat_enum_alias(self):
        src = inspect.getsource(route_renderer._apply_stops_style)
        assert "P.OverPoint" not in src, (
            "FOLLOWUP regression: must not use flat enum P.OverPoint "
            "(broken in PyQt6)"
        )


class TestBlockerD:
    """Click-to-zoom must be CRS-aware, not raw setCenter(lon,lat)."""

    def test_on_item_clicked_uses_crs_transform(self):
        # directions_dock can't be imported outside QGIS; read source directly
        dock_path = os.path.join(
            os.path.dirname(__file__), "..", "ui", "directions_dock.py",
        )
        with open(dock_path) as f:
            src = f.read()
        assert "QgsCoordinateTransform" in src, (
            "BLOCKER-D regression: _on_item_clicked must use "
            "QgsCoordinateTransform before canvas.setCenter()"
        )

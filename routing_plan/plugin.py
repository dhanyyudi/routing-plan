import os

from qgis.PyQt.QtGui import QIcon, QAction

from .core import ValhallaNavigatorCore


class ValhallaNavigatorPlugin:
    """QGIS hookpoint. Installs a top-level "Routing Plan" menu in the
    main menu bar (next to Processing / Window / Help) plus a toolbar
    button. Mirrors the menu-bar pattern used by HCMGIS and similar
    feature-rich plugins so the seven Routing Plan workflows are
    discoverable without digging into Plugins → ..."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.menu = None  # set to QMenu in initGui
        self.toolbar = None
        self.core = None
        self.actions = []

    # ── menu construction helpers ──────────────────────────────

    def _make_action(self, label, callback, icon=None):
        action = QAction(icon, label, self.iface.mainWindow()) if icon \
            else QAction(label, self.iface.mainWindow())
        action.triggered.connect(callback)
        self.menu.addAction(action)
        self.actions.append(action)
        return action

    def _add_separator(self):
        """Add a real Qt menu separator (not a QAction with dashes)."""
        sep = QAction(self.iface.mainWindow())
        sep.setSeparator(True)
        self.menu.addAction(sep)
        self.actions.append(sep)

    # ── lifecycle ──────────────────────────────────────────────

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.svg")
        icon = QIcon(icon_path)

        # Create the top-level menu in the main menu bar.
        menubar = self.iface.mainWindow().menuBar()
        self.menu = menubar.addMenu("&Routing Plan")

        # Compute Route (main dialog) — keep the icon for the toolbar.
        self.compute_route_action = self._make_action(
            "Compute Route…", self.run, icon=icon,
        )
        self.compute_route_action.setToolTip(
            "Open Routing Plan — compute route from waypoints"
        )

        self._add_separator()

        # Feature dialogs — listed in the same order the v0.2.0 plan
        # numbers them so any future hand-off references line up.
        self.isochrone_action = self._make_action(
            "Isochrones…", self.open_isochrone,
        )
        self.matrix_action = self._make_action(
            "OD Matrix…", self.open_matrix,
        )
        self.match_action = self._make_action(
            "Map Matching…", self.open_match,
        )
        self.locate_action = self._make_action(
            "Snap to Road…", self.open_locate,
        )
        self.elevation_action = self._make_action(
            "Elevation Profile…", self.open_elevation,
        )

        self._add_separator()

        self.expansion_action = self._make_action(
            "Expansion (debug)…", self.open_expansion,
        )

        self._add_separator()

        self.settings_action = self._make_action(
            "Settings…", self.open_settings,
        )

        # Toolbar — single button (the main Compute Route action).
        self.toolbar = self.iface.addToolBar("Routing Plan")
        self.toolbar.setObjectName("RoutingPlanToolbar")
        self.toolbar.addAction(self.compute_route_action)

        self.core = ValhallaNavigatorCore(self.iface)

    def unload(self):
        # Remove the toolbar button (each QAction was added once to
        # the toolbar via addAction).
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
        # Drop the top-level menu from the main menu bar.
        if self.menu is not None:
            menubar = self.iface.mainWindow().menuBar()
            menubar.removeAction(self.menu.menuAction())
            self.menu = None
        if self.toolbar is not None:
            del self.toolbar
            self.toolbar = None
        if self.core is not None:
            self.core.unload()
            self.core = None
        self.actions = []

    # ── slots ──────────────────────────────────────────────────

    def run(self):
        self.core.show_main_dialog()

    def open_settings(self):
        self.core.show_settings_dialog()

    def open_isochrone(self):
        from .ui.isochrone_dialog import IsochroneDialog
        dlg = IsochroneDialog(self.iface, self.core)
        dlg.exec()

    def open_matrix(self):
        from .ui.matrix_dialog import MatrixDialog
        dlg = MatrixDialog(self.iface, self.core)
        dlg.exec()

    def open_match(self):
        from .ui.match_dialog import MatchDialog
        dlg = MatchDialog(self.iface, self.core)
        dlg.exec()

    def open_expansion(self):
        from .ui.expansion_dialog import ExpansionDialog
        dlg = ExpansionDialog(self.iface, self.core)
        dlg.exec()

    def open_elevation(self):
        from .ui.elevation_dialog import ElevationDialog
        dlg = ElevationDialog(self.iface, self.core)
        dlg.exec()

    def open_locate(self):
        from .ui.locate_dialog import LocateDialog
        dlg = LocateDialog(self.iface, self.core)
        dlg.exec()

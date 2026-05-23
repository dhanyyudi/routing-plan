import os

from qgis.PyQt.QtGui import QIcon, QAction
from qgis.PyQt.QtWidgets import QToolBar

from .core import ValhallaNavigatorCore


class ValhallaNavigatorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&Routing Plan"
        self.toolbar = None
        self.core = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.svg")
        icon = QIcon(icon_path)

        self.compute_route_action = QAction(
            icon, "Compute Route…", self.iface.mainWindow()
        )
        self.compute_route_action.triggered.connect(self.run)
        self.compute_route_action.setToolTip(
            "Open Routing Plan — compute route from waypoints"
        )

        self.iface.addPluginToMenu(self.menu, self.compute_route_action)

        self.settings_action = QAction("Settings…", self.iface.mainWindow())
        self.settings_action.triggered.connect(self.open_settings)
        self.iface.addPluginToMenu(self.menu, self.settings_action)

        self.toolbar = self.iface.addToolBar("Routing Plan")
        self.toolbar.setObjectName("RoutingPlanToolbar")
        self.toolbar.addAction(self.compute_route_action)

        self.actions.extend([self.compute_route_action, self.settings_action])

        self.core = ValhallaNavigatorCore(self.iface)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.toolbar:
            del self.toolbar
        if self.core:
            self.core.unload()

    def run(self):
        self.core.show_main_dialog()

    def open_settings(self):
        self.core.show_settings_dialog()

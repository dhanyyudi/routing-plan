from .valhalla_client import ValhallaClient
from .route_renderer import build_route_layer, build_maneuvers_layer, build_stops_layer


def _build_client(engine=None):
    """Factory: return a client for the given engine, or for the
    current ``PluginSettings.get_engine()`` value if ``engine`` is
    ``None``.

    Pass an explicit ``engine`` from feature dialogs whose engine
    combo is locked (Isochrones, Expansion, Elevation) — that way
    they always get the right client regardless of what other
    dialogs have done with the global setting.
    """
    from .settings import PluginSettings
    eng = engine if engine is not None else PluginSettings.get_engine()
    if eng == "osrm":
        from .osrm_client import OSRMClient
        endpoint = PluginSettings.get_endpoint_for("osrm")
        timeout = PluginSettings.get_timeout()
        return OSRMClient(endpoint=endpoint, timeout=timeout)
    else:
        endpoint = PluginSettings.get_endpoint_for("valhalla")
        timeout = PluginSettings.get_timeout()
        return ValhallaClient(endpoint=endpoint, timeout=timeout)


def client_for(engine):
    """Public helper for feature dialogs: build a fresh client for
    the *specified* engine, independent of the global setting and
    without mutating ``ValhallaNavigatorCore.client``."""
    return _build_client(engine)


class ValhallaNavigatorCore:
    def __init__(self, iface):
        self.iface = iface
        from .settings import PluginSettings
        self._settings = PluginSettings
        self.client = _build_client()
        self.dock = None
        self._last_response = None
        self._active_task = None
        self._progress_item = None
        self._progress_bar = None

    def _rebuild_client(self):
        """Re-create the client after an engine or endpoint change."""
        self.client = _build_client()

    def show_main_dialog(self):
        from ..ui.main_dialog import MainDialog
        dlg = MainDialog(self.iface, self)
        dlg.exec()

    def show_settings_dialog(self):
        from ..i18n import tr
        from ..ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.iface.mainWindow())
        if dlg.exec():
            self._rebuild_client()
            self.iface.messageBar().pushSuccess("Routing Plan", tr("settings_saved"))

    def _demo_flow(self):
        import json
        import os

        fixture_path = os.path.join(
            os.path.dirname(__file__), "..", "tests", "fixtures", "valhalla_response_mock.json"
        )
        try:
            with open(fixture_path) as f:
                response = json.load(f)
            self._on_route_done(response)
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Demo flow error: {e}", "Routing Plan", Qgis.Critical)

    def compute_route(self, waypoints, costing=None, costing_options=None,
                      directions_options=None, optimized=False, date_time=None):
        from ..i18n import tr
        self._last_lang = (directions_options or {}).get("language", "en")
        if costing is None:
            costing = self._settings.get_default_costing()
        from .route_task import RouteTask

        task = RouteTask(
            tr("calculating_route"),
            self.client,
            waypoints,
            costing=costing,
            costing_options=costing_options,
            directions_options=directions_options,
            optimized=optimized,
            date_time=date_time,
        )
        task.taskCompleted.connect(lambda: self._on_task_completed(task))
        task.taskTerminated.connect(lambda: self._on_task_failed(task))

        self._active_task = task
        self._show_progress()

        from qgis.core import QgsApplication
        QgsApplication.taskManager().addTask(task)

    def _show_progress(self):
        from ..i18n import tr
        from qgis.core import Qgis
        from qgis.PyQt.QtWidgets import QProgressBar, QPushButton, QWidget, QHBoxLayout

        msg = self.iface.messageBar().createMessage("Routing Plan", tr("calculating_route"))
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)
        self._progress_bar.setFixedWidth(200)

        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.setFixedHeight(24)
        cancel_btn.clicked.connect(self._cancel_task)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._progress_bar)
        layout.addWidget(cancel_btn)

        msg.layout().addWidget(container)
        self._progress_item = msg
        self.iface.messageBar().pushWidget(msg, Qgis.Info)

    def _cancel_task(self):
        if self._active_task:
            self._active_task.cancel()
        self._clear_progress()

    def _clear_progress(self):
        if self._progress_item:
            self.iface.messageBar().popWidget(self._progress_item)
            self._progress_item = None
        self._progress_bar = None

    def _on_task_completed(self, task):
        from ..i18n import tr
        self._clear_progress()
        self._active_task = None
        if task.isCanceled():
            self.iface.messageBar().pushInfo("Routing Plan", tr("route_cancelled"))
            return
        if task.result_ok and task.response:
            self._on_route_done(task.response)
        else:
            self._on_task_failed(task)

    def _on_task_failed(self, task):
        from ..i18n import tr
        self._clear_progress()
        self._active_task = None
        if task.isCanceled():
            return
        error = task.error
        if error:
            self._show_error(error)
        else:
            self.iface.messageBar().pushCritical("Routing Plan", tr("route_failed"))

    def _clear_previous_routing_plan(self):
        from qgis.core import QgsProject

        project = QgsProject.instance()
        root = project.layerTreeRoot()
        group = root.findGroup("Routing Plan")
        if group is None:
            return

        layer_ids = [c.layer().id() for c in group.findLayers() if c.layer()]
        if layer_ids:
            project.removeMapLayers(layer_ids)
        root.removeChildNode(group)

    def _on_route_done(self, response):
        from ..i18n import tr
        from .settings import PluginSettings

        if PluginSettings.get_auto_clear_previous():
            self._clear_previous_routing_plan()

        try:
            route_layer = build_route_layer(response)
            maneuvers_layer = build_maneuvers_layer(response)
            stops_layer = build_stops_layer(response)
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"Renderer error: {e}", "Routing Plan", Qgis.Critical)
            self.iface.messageBar().pushCritical("Routing Plan", tr("render_failed", error=str(e)))
            return

        if self.dock is None:
            from ..ui.directions_dock import DirectionsDock
            self.dock = DirectionsDock(self.iface)
        self._last_response = response
        self.dock.show(response, route_layer, maneuvers_layer, self._last_lang)

        canvas = self.iface.mapCanvas()
        target_layer = stops_layer if stops_layer else route_layer
        if target_layer:
            layer_extent = target_layer.extent()
            canvas_extent = canvas.mapSettings().layerExtentToOutputExtent(target_layer, layer_extent)
            canvas_extent.scale(1.05)
            canvas.setExtent(canvas_extent)
        canvas.refresh()

    def _show_error(self, error):
        from ..i18n import tr
        from qgis.PyQt.QtWidgets import QMessageBox

        if error.kind == "no_route":
            QMessageBox.warning(
                self.iface.mainWindow(),
                tr("no_route_title"),
                tr("no_route_message", detail=error.message),
            )
        elif error.kind == "out_of_coverage":
            self.iface.messageBar().pushWarning(
                "Routing Plan",
                tr("out_of_coverage", detail=error.message),
            )
        else:
            self.iface.messageBar().pushCritical(
                "Routing Plan",
                tr("error_with_code", message=error.message, code=error.code),
            )

    def unload(self):
        if self._active_task:
            self._active_task.cancel()
        if self.dock:
            self.dock.unload()
            self.dock = None

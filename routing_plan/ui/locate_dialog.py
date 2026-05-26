"""Snap to Road / Locate dialog — nearest road lookup (F7)."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QGroupBox, QHeaderView,
)
from qgis.core import QgsCoordinateTransform, QgsProject

from ..core.core import client_for
from ..core.engine import VALHALLA_COSTINGS
from ..core.settings import PluginSettings
from ..i18n import tr


class LocateDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("locate_title"))
        self.setMinimumSize(450, 400)
        self._map_tool = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Engine
        eng_row = QHBoxLayout()
        eng_row.addWidget(QLabel(tr("engine_label")))
        self.engine_combo = QComboBox()
        self.engine_combo.addItem(tr("engine_valhalla"), "valhalla")
        self.engine_combo.addItem(tr("engine_osrm"), "osrm")
        eng = PluginSettings.get_engine()
        idx = self.engine_combo.findData(eng)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)
        eng_row.addWidget(self.engine_combo)
        eng_row.addStretch()
        layout.addLayout(eng_row)

        # Costing (Valhalla only)
        self.costing_combo = QComboBox()
        for val, label in VALHALLA_COSTINGS:
            self.costing_combo.addItem(label, val)
        cf = QFormLayout()
        cf.addRow("Costing:", self.costing_combo)
        layout.addLayout(cf)

        # Input point
        pt_group = QGroupBox(tr("locate_input_label"))
        pl = QFormLayout(pt_group)
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setValue(-6.2088)
        pl.addRow("Latitude:", self.lat_spin)
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setValue(106.8456)
        pl.addRow("Longitude:", self.lon_spin)
        self.pick_btn = QPushButton(tr("locate_pick_on_map"))
        pl.addRow("", self.pick_btn)
        layout.addWidget(pt_group)

        # Number of results
        nf = QFormLayout()
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10)
        self.count_spin.setValue(1)
        nf.addRow(tr("locate_count"), self.count_spin)
        layout.addLayout(nf)

        # Results preview
        self.result_table = QTableWidget(0, 4)
        self.result_table.setHorizontalHeaderLabels(["Rank", "Name", "Distance (m)", "Road Class"])
        hdr = self.result_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.result_table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("locate_compute"))
        self.compute_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; padding: 8px 24px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #1557b0; }"
        )
        btn_layout.addWidget(self.compute_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self.pick_btn.clicked.connect(self._pick_on_map)
        self.compute_btn.clicked.connect(self._on_compute)

    def _on_engine_changed(self):
        engine = self.engine_combo.currentData() or "valhalla"
        self.costing_combo.setVisible(engine == "valhalla")

    def _pick_on_map(self):
        from qgis.gui import QgsMapToolEmitPoint

        canvas = self.iface.mapCanvas()
        self._map_tool = QgsMapToolEmitPoint(canvas)
        self._map_tool.canvasClicked.connect(self._on_map_clicked)
        canvas.setMapTool(self._map_tool)
        self.pick_btn.setText(tr("locate_pick_active"))
        self.pick_btn.setStyleSheet("background-color: #1973f5; color: white;")
        self.iface.messageBar().pushInfo("Routing Plan", tr("locate_pick_hint"))

    def _on_map_clicked(self, point, button):
        from qgis.core import QgsCoordinateReferenceSystem

        canvas = self.iface.mapCanvas()
        crs = canvas.mapSettings().destinationCrs()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        if crs != wgs84:
            transform = QgsCoordinateTransform(crs, wgs84, QgsProject.instance())
            point = transform.transform(point)
        self.lat_spin.setValue(point.y())
        self.lon_spin.setValue(point.x())
        canvas.unsetMapTool(self._map_tool)
        self._map_tool = None
        self.pick_btn.setText(tr("locate_pick_on_map"))
        self.pick_btn.setStyleSheet("")
        self.iface.messageBar().pushSuccess(
            "Routing Plan",
            tr("locate_pick_captured", lat=f"{point.y():.6f}", lon=f"{point.x():.6f}"),
        )

    def _on_compute(self):
        lat = self.lat_spin.value()
        lon = self.lon_spin.value()
        engine = self.engine_combo.currentData() or "valhalla"
        count = self.count_spin.value()

        from qgis.core import QgsTask, QgsApplication

        class LocateTask(QgsTask):
            def __init__(self, desc, client, lat, lon, engine, count, costing):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._lat = lat
                self._lon = lon
                self._engine = engine
                self._count = count
                self._costing = costing
                self.response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    if self._engine == "osrm":
                        self.response = self._client.locate(self._lat, self._lon, self._count)
                    else:
                        self.response = self._client.locate(
                            [{"lat": self._lat, "lon": self._lon}], self._costing,
                        )
                        # Normalize Valhalla response to common shape
                        raw_results = self.response.get("edges", []) or self.response.get("results", [])
                        results = []
                        for r in raw_results[:self._count]:
                            results.append({
                                "lat": r.get("correlated_lat", r.get("lat", self._lat)),
                                "lon": r.get("correlated_lon", r.get("lon", self._lon)),
                                "name": r.get("names", [""])[0] if r.get("names") else "",
                                "distance_m": r.get("distance", 0) * 1000
                                if r.get("distance", 0) < 100 else r.get("distance", 0),
                                "way_ids": r.get("way_ids", r.get("way_id", [])),
                                "road_class": r.get("road_class", ""),
                            })
                        self.response = {"results": results}
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

        task = LocateTask(
            tr("locate_loading"), client_for(engine), lat, lon, engine, count,
            self.costing_combo.currentData(),
        )
        task.taskCompleted.connect(lambda: self._on_locate_done(task, lat, lon))
        task.taskTerminated.connect(lambda: self._on_locate_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_locate_done(self, task, input_lat, input_lon):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.locate_renderer import build_locate_point_layer, build_input_marker_layer

                engine = self.engine_combo.currentData() or "valhalla"
                build_locate_point_layer(task.response, engine)
                build_input_marker_layer(input_lat, input_lon)

                # Populate preview table
                results = task.response.get("results", [])
                self.result_table.setRowCount(len(results))
                for i, r in enumerate(results):
                    self.result_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.result_table.setItem(i, 1, QTableWidgetItem(r.get("name", "")))
                    self.result_table.setItem(
                        i, 2, QTableWidgetItem(str(round(r.get("distance_m", 0), 1))),
                    )
                    self.result_table.setItem(i, 3, QTableWidgetItem(r.get("road_class", "")))

                if results:
                    self.iface.messageBar().pushSuccess("Routing Plan", f"{len(results)} result(s) found")
                else:
                    self.iface.messageBar().pushWarning("Routing Plan", tr("locate_no_results"))
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_locate_failed(task)

    def _on_locate_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Locate failed: {msg}")

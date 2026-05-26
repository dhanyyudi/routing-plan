"""Isochrones dialog — reachability analysis (Valhalla-only, F2).

One origin point + 1–4 contour values (time in minutes or distance in km)
→ rendered as semi-transparent polygons on the canvas.
"""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QAbstractItemView,
)
from qgis.PyQt.QtGui import QColor

from ..core.core import client_for
from ..core.engine import VALHALLA_COSTINGS
from ..i18n import tr

DEFAULT_CONTOUR_COLORS = ["bf4040", "bf8040", "bfbf40", "40bf40"]


class IsochroneDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("iso_title"))
        self.setMinimumSize(500, 400)
        self._map_tool = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Engine (locked to Valhalla)
        eng_row = QHBoxLayout()
        eng_row.addWidget(QLabel(tr("engine_label")))
        self.engine_combo = QComboBox()
        self.engine_combo.addItem(tr("engine_valhalla"), "valhalla")
        self.engine_combo.setEnabled(False)
        self.engine_combo.setToolTip("Isochrones are Valhalla-only")
        eng_row.addWidget(self.engine_combo)
        eng_row.addStretch()
        layout.addLayout(eng_row)

        # Costing
        form = QFormLayout()
        self.costing_combo = QComboBox()
        for val, label in VALHALLA_COSTINGS:
            self.costing_combo.addItem(label, val)
        form.addRow("Costing:", self.costing_combo)
        layout.addLayout(form)

        # Origin
        origin_group = QGroupBox(tr("iso_origin"))
        olayout = QFormLayout(origin_group)
        self.origin_lat = QDoubleSpinBox()
        self.origin_lat.setRange(-90, 90)
        self.origin_lat.setDecimals(6)
        self.origin_lat.setValue(-6.2088)  # Jakarta
        olayout.addRow("Latitude:", self.origin_lat)
        self.origin_lon = QDoubleSpinBox()
        self.origin_lon.setRange(-180, 180)
        self.origin_lon.setDecimals(6)
        self.origin_lon.setValue(106.8456)
        olayout.addRow("Longitude:", self.origin_lon)
        self.pick_btn = QPushButton(tr("iso_pick_on_map"))
        olayout.addRow("", self.pick_btn)
        layout.addWidget(origin_group)

        # Contours table
        cont_group = QGroupBox(tr("iso_contours_label"))
        clayout = QVBoxLayout(cont_group)

        self.contour_table = QTableWidget(4, 3)
        self.contour_table.setHorizontalHeaderLabels(["Metric", "Value", "Color"])
        hdr = self.contour_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.contour_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Default: 5/10/15 minutes
        defaults = [(tr("iso_metric_time"), 5), (tr("iso_metric_time"), 10),
                    (tr("iso_metric_time"), 15), (tr("iso_metric_time"), 20)]
        for row, (metric, val) in enumerate(defaults):
            self.contour_table.setItem(row, 0, QTableWidgetItem(metric))
            self.contour_table.setItem(row, 1, QTableWidgetItem(str(val)))
            color = DEFAULT_CONTOUR_COLORS[row] if row < len(DEFAULT_CONTOUR_COLORS) else "bfbf40"
            item = QTableWidgetItem(color)
            item.setBackground(QColor("#" + color))
            self.contour_table.setItem(row, 2, item)

        clayout.addWidget(self.contour_table)

        btn_row = QHBoxLayout()
        self.add_row_btn = QPushButton("+")
        self.add_row_btn.setFixedWidth(40)
        btn_row.addWidget(self.add_row_btn)
        self.remove_row_btn = QPushButton("-")
        self.remove_row_btn.setFixedWidth(40)
        btn_row.addWidget(self.remove_row_btn)
        btn_row.addStretch()
        clayout.addLayout(btn_row)
        layout.addWidget(cont_group)

        # Options
        opts_form = QFormLayout()
        self.polygons_check = QCheckBox()
        self.polygons_check.setChecked(True)
        opts_form.addRow(tr("iso_polygons"), self.polygons_check)

        self.denoise_spin = QDoubleSpinBox()
        self.denoise_spin.setRange(0.0, 1.0)
        self.denoise_spin.setSingleStep(0.1)
        self.denoise_spin.setValue(1.0)
        opts_form.addRow(tr("iso_denoise"), self.denoise_spin)

        self.generalize_spin = QSpinBox()
        self.generalize_spin.setRange(0, 10000)
        self.generalize_spin.setSingleStep(50)
        self.generalize_spin.setSuffix(" m")
        self.generalize_spin.setValue(0)
        opts_form.addRow(tr("iso_generalize"), self.generalize_spin)
        layout.addLayout(opts_form)

        # Compute button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("iso_compute"))
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
        self.pick_btn.clicked.connect(self._pick_on_map)
        self.compute_btn.clicked.connect(self._on_compute)
        self.add_row_btn.clicked.connect(self._add_contour_row)
        self.remove_row_btn.clicked.connect(self._remove_contour_row)

    def _add_contour_row(self):
        row = self.contour_table.rowCount()
        if row >= 8:
            return
        self.contour_table.setRowCount(row + 1)
        self.contour_table.setItem(row, 0, QTableWidgetItem(tr("iso_metric_time")))
        self.contour_table.setItem(row, 1, QTableWidgetItem("0"))
        color = DEFAULT_CONTOUR_COLORS[row % len(DEFAULT_CONTOUR_COLORS)]
        item = QTableWidgetItem(color)
        item.setBackground(QColor("#" + color))
        self.contour_table.setItem(row, 2, item)

    def _remove_contour_row(self):
        rows = sorted({i.row() for i in self.contour_table.selectedIndexes()}, reverse=True)
        if not rows:
            if self.contour_table.rowCount() > 1:
                self.contour_table.setRowCount(self.contour_table.rowCount() - 1)
            return
        for row in rows:
            self.contour_table.removeRow(row)

    def _pick_on_map(self):
        from qgis.gui import QgsMapToolEmitPoint

        canvas = self.iface.mapCanvas()
        self._map_tool = QgsMapToolEmitPoint(canvas)
        self._map_tool.canvasClicked.connect(self._on_map_clicked)
        canvas.setMapTool(self._map_tool)
        self.pick_btn.setText(tr("iso_pick_active"))
        self.pick_btn.setStyleSheet("background-color: #1973f5; color: white;")
        self.iface.messageBar().pushInfo(
            "Routing Plan",
            tr("iso_pick_hint"),
        )

    def _on_map_clicked(self, point, button):
        from qgis.core import (
            QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject,
        )

        canvas = self.iface.mapCanvas()
        crs = canvas.mapSettings().destinationCrs()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        if crs != wgs84:
            transform = QgsCoordinateTransform(crs, wgs84, QgsProject.instance())
            point = transform.transform(point)
        self.origin_lat.setValue(point.y())
        self.origin_lon.setValue(point.x())
        canvas.unsetMapTool(self._map_tool)
        self._map_tool = None
        self.pick_btn.setText(tr("iso_pick_on_map"))
        self.pick_btn.setStyleSheet("")
        self.iface.messageBar().pushSuccess(
            "Routing Plan",
            tr("iso_pick_captured", lat=f"{point.y():.6f}", lon=f"{point.x():.6f}"),
        )

    def _get_contours(self):
        contours = []
        for row in range(self.contour_table.rowCount()):
            metric_item = self.contour_table.item(row, 0)
            val_item = self.contour_table.item(row, 1)
            color_item = self.contour_table.item(row, 2)
            if not (metric_item and val_item):
                continue
            try:
                value = float(val_item.text())
            except ValueError:
                continue
            if value <= 0:
                continue
            metric = "time" if tr("iso_metric_time") == metric_item.text() else "distance"
            color = color_item.text() if color_item else "40bf40"
            entry = {"color": color}
            entry[metric] = value
            contours.append(entry)
        return contours

    def _on_compute(self):
        contours = self._get_contours()
        if not contours:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "No valid contours defined")
            return

        location = {"lat": self.origin_lat.value(), "lon": self.origin_lon.value()}
        costing = self.costing_combo.currentData()

        from ..core.isochrone_renderer import build_isochrone_layer  # noqa: F401
        from ..core.settings import PluginSettings
        from qgis.core import QgsProject, QgsTask, QgsApplication  # noqa: F401

        if PluginSettings.get_auto_clear_previous():
            project = QgsProject.instance()
            root = project.layerTreeRoot()
            group = root.findGroup("Routing Plan")
            if group:
                iso_layers = [c.layer() for c in group.findLayers()
                              if c.layer() and c.layer().name() == tr("iso_layer_name")]
                if iso_layers:
                    project.removeMapLayers([lyr.id() for lyr in iso_layers])

        class IsochroneTask(QgsTask):
            def __init__(self, desc, client, loc, cost, contours, poly, denoise, generalize):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._loc = loc
                self._cost = cost
                self._contours = contours
                self._poly = poly
                self._denoise = denoise
                self._gen = generalize
                self.response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    self.response = self._client.isochrone(
                        self._loc, self._cost, self._contours,
                        polygons=self._poly, denoise=self._denoise,
                        generalize=self._gen,
                    )
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

            def finished(self, result):
                pass

        task = IsochroneTask(
            tr("iso_compute"), client_for("valhalla"), location, costing, contours,
            self.polygons_check.isChecked(), self.denoise_spin.value(),
            self.generalize_spin.value() if self.generalize_spin.value() > 0 else None,
        )

        task.taskCompleted.connect(lambda: self._on_isochrone_done(task))
        task.taskTerminated.connect(lambda: self._on_isochrone_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_isochrone_done(self, task):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.isochrone_renderer import build_isochrone_layer
                build_isochrone_layer(task.response, tr("iso_layer_name"))
                self.iface.messageBar().pushSuccess("Routing Plan", "Isochrones computed")
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_isochrone_failed(task)

    def _on_isochrone_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Isochrone failed: {msg}")

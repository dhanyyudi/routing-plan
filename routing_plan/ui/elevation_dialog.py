"""Elevation Profile dialog — height sampling along a path (Valhalla-only, F6)."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QRadioButton,
    QGroupBox, QFileDialog, QMessageBox, QButtonGroup, QPlainTextEdit,
)
from qgis.core import QgsProject, Qgis

from ..core.core import client_for
from ..i18n import tr


class ElevationDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("elev_title"))
        self.setMinimumSize(500, 400)
        self._last_response = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Engine (locked)
        eng_row = QHBoxLayout()
        eng_row.addWidget(QLabel(tr("engine_label")))
        self.engine_combo = QComboBox()
        self.engine_combo.addItem(tr("engine_valhalla"), "valhalla")
        self.engine_combo.setEnabled(False)
        self.engine_combo.setToolTip("Elevation is Valhalla-only")
        eng_row.addWidget(self.engine_combo)
        eng_row.addStretch()
        layout.addLayout(eng_row)

        # Source
        src_group = QGroupBox("Source")
        sv = QVBoxLayout(src_group)
        self.source_group = QButtonGroup(self)
        self.rb_route = QRadioButton(tr("elev_source_route"))
        self.rb_layer = QRadioButton(tr("elev_source_layer"))
        self.rb_polyline = QRadioButton(tr("elev_source_polyline"))
        self.source_group.addButton(self.rb_route, 0)
        self.source_group.addButton(self.rb_layer, 1)
        self.source_group.addButton(self.rb_polyline, 2)
        self.rb_route.setChecked(True)
        sv.addWidget(self.rb_route)
        sv.addWidget(self.rb_layer)
        sv.addWidget(self.rb_polyline)

        self.layer_combo = QComboBox()
        self._populate_layers()
        self.layer_combo.setVisible(False)
        sv.addWidget(self.layer_combo)

        self.polyline_edit = QPlainTextEdit()
        self.polyline_edit.setPlaceholderText("Paste encoded polyline here…")
        self.polyline_edit.setMaximumHeight(80)
        self.polyline_edit.setVisible(False)
        sv.addWidget(self.polyline_edit)

        layout.addWidget(src_group)

        # Resample
        form = QFormLayout()
        self.resample_spin = QSpinBox()
        self.resample_spin.setRange(0, 10000)
        self.resample_spin.setSingleStep(100)
        self.resample_spin.setSuffix(" m")
        form.addRow(tr("elev_resample"), self.resample_spin)
        layout.addLayout(form)

        # Stats labels
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("elev_compute"))
        self.compute_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; padding: 8px 24px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #1557b0; }"
        )
        btn_layout.addWidget(self.compute_btn)
        self.export_btn = QPushButton(tr("elev_export_csv"))
        btn_layout.addWidget(self.export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_layers(self):
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        for lyr in layers:
            if lyr.type() == Qgis.LayerType.Vector and hasattr(lyr, "geometryType"):
                gt = lyr.geometryType()
                if gt == 1:  # Line
                    self.layer_combo.addItem(lyr.name(), lyr.id())

    def _connect_signals(self):
        self.rb_route.toggled.connect(lambda: self._on_source_changed())
        self.rb_layer.toggled.connect(lambda: self._on_source_changed())
        self.rb_polyline.toggled.connect(lambda: self._on_source_changed())
        self.compute_btn.clicked.connect(self._on_compute)
        self.export_btn.clicked.connect(self._export_csv)

    def _on_source_changed(self):
        self.layer_combo.setVisible(self.rb_layer.isChecked())
        self.polyline_edit.setVisible(self.rb_polyline.isChecked())

    def _get_polyline(self):
        if self.rb_route.isChecked() and self.core._last_response:
            legs = self.core._last_response.get("trip", {}).get("legs", [])
            shapes = [leg.get("shape", "") for leg in legs if leg.get("shape")]
            return "".join(shapes)
        if self.rb_polyline.isChecked():
            return self.polyline_edit.toPlainText().strip()
        if self.rb_layer.isChecked():
            layer_id = self.layer_combo.currentData()
            if not layer_id:
                return ""
            layer = QgsProject.instance().mapLayer(layer_id)
            if not layer:
                return ""
            coords = []
            from ..core.waypoint_loader import load_trace_from_layer
            trace = load_trace_from_layer(layer)
            for pt in trace:
                coords.append(f"{pt['lon']},{pt['lat']}")
            return ";".join(coords)
        return ""

    def _on_compute(self):
        polyline = self._get_polyline()
        if not polyline:
            QMessageBox.warning(self, "Error", "No route or polyline available")
            return

        resample = self.resample_spin.value() if self.resample_spin.value() > 0 else None

        from qgis.core import QgsTask, QgsApplication

        class ElevationTask(QgsTask):
            def __init__(self, desc, client, poly, resample):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._poly = poly
                self._resample = resample
                self.response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    self.response = self._client.height(
                        encoded_polyline=self._poly, range=True,
                        resample_distance=self._resample,
                    )
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

        task = ElevationTask(tr("elev_loading"), client_for("valhalla"), polyline, resample)
        task.taskCompleted.connect(lambda: self._on_elevation_done(task))
        task.taskTerminated.connect(lambda: self._on_elevation_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_elevation_done(self, task):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.elevation_renderer import build_elevation_table, compute_elevation_stats
                self._last_response = task.response
                build_elevation_table(task.response)
                stats = compute_elevation_stats(task.response)
                self.stats_label.setText(
                    f"Min: {stats['min']} m  |  Max: {stats['max']} m  |  "
                    f"{tr('elev_ascent')}: {stats['total_ascent']} m  |  "
                    f"{tr('elev_descent')}: {stats['total_descent']} m"
                )
                self.iface.messageBar().pushSuccess("Routing Plan", "Elevation computed")
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_elevation_failed(task)

    def _on_elevation_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Elevation failed: {msg}")

    def _export_csv(self):
        if not self._last_response:
            QMessageBox.information(self, "Info", "Compute elevation first")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            from ..core.exporter import export_elevation_csv
            export_elevation_csv(self._last_response, path)
            QMessageBox.information(self, "Export", f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

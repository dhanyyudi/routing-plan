"""Map Matching dialog — snap GPS traces to roads (F4)."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QRadioButton,
    QGroupBox, QFileDialog, QMessageBox, QButtonGroup, QPlainTextEdit,
)
from qgis.core import QgsProject, Qgis

from ..core.core import client_for
from ..core.engine import costings_for
from ..core.settings import PluginSettings
from ..i18n import tr


class MatchDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("match_title"))
        self.setMinimumSize(500, 400)
        self._trace_points = []
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

        # Costing
        form = QFormLayout()
        self.costing_combo = QComboBox()
        self._populate_costing()
        form.addRow("Costing:", self.costing_combo)
        layout.addLayout(form)

        # Source group
        src_group = QGroupBox("Trace Source")
        sv = QVBoxLayout(src_group)

        self.source_group = QButtonGroup(self)
        self.rb_layer = QRadioButton(tr("match_source_layer"))
        self.rb_csv = QRadioButton(tr("match_source_csv"))
        self.rb_polyline = QRadioButton(tr("match_source_polyline"))
        self.source_group.addButton(self.rb_layer, 0)
        self.source_group.addButton(self.rb_csv, 1)
        self.source_group.addButton(self.rb_polyline, 2)
        self.rb_layer.setChecked(True)
        sv.addWidget(self.rb_layer)
        sv.addWidget(self.rb_csv)
        sv.addWidget(self.rb_polyline)

        self.layer_combo = QComboBox()
        self._populate_layers()
        sv.addWidget(self.layer_combo)

        self.load_csv_btn = QPushButton("Browse CSV…")
        self.load_csv_btn.setVisible(False)
        sv.addWidget(self.load_csv_btn)

        self.polyline_edit = QPlainTextEdit()
        self.polyline_edit.setPlaceholderText("Paste encoded polyline here…")
        self.polyline_edit.setMaximumHeight(80)
        self.polyline_edit.setVisible(False)
        sv.addWidget(self.polyline_edit)

        layout.addWidget(src_group)

        # Shape match (Valhalla only)
        self.shape_match_combo = QComboBox()
        self.shape_match_combo.addItem("walk_or_snap", "walk_or_snap")
        self.shape_match_combo.addItem("map_snap", "map_snap")
        self.shape_match_combo.addItem("edge_walk", "edge_walk")
        sm_form = QFormLayout()
        sm_form.addRow(tr("match_shape_match"), self.shape_match_combo)
        layout.addLayout(sm_form)

        # Attributes checkbox (Valhalla only)
        self.attributes_check = QCheckBox(tr("match_with_attributes"))
        layout.addWidget(self.attributes_check)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("match_compute"))
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

    def _populate_costing(self):
        self.costing_combo.clear()
        engine = self.engine_combo.currentData() or "valhalla"
        for val, label in costings_for(engine):
            self.costing_combo.addItem(label, val)

    def _populate_layers(self):
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        for lyr in layers:
            if lyr.type() == Qgis.LayerType.Vector:
                self.layer_combo.addItem(lyr.name(), lyr.id())

    def _connect_signals(self):
        self.engine_combo.currentIndexChanged.connect(lambda: self._populate_costing())
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self.rb_layer.toggled.connect(lambda: self._on_source_changed())
        self.rb_csv.toggled.connect(lambda: self._on_source_changed())
        self.rb_polyline.toggled.connect(lambda: self._on_source_changed())
        self.load_csv_btn.clicked.connect(self._load_csv)
        self.compute_btn.clicked.connect(self._on_compute)

    def _on_engine_changed(self):
        engine = self.engine_combo.currentData() or "valhalla"
        is_valhalla = (engine == "valhalla")
        self.shape_match_combo.setVisible(is_valhalla)
        self.attributes_check.setVisible(is_valhalla)
        if not is_valhalla:
            self.attributes_check.setChecked(False)

    def _on_source_changed(self):
        is_layer = self.rb_layer.isChecked()
        is_csv = self.rb_csv.isChecked()
        self.layer_combo.setVisible(is_layer)
        self.load_csv_btn.setVisible(is_csv)
        self.polyline_edit.setVisible(not is_layer and not is_csv)

    def _load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load trace", "", "CSV (*.csv)")
        if not path:
            return
        from ..core.waypoint_loader import load_csv
        self._trace_points = load_csv(path)
        QMessageBox.information(self, "Loaded", f"{len(self._trace_points)} points loaded")

    def _get_shape_string(self):
        if self.rb_polyline.isChecked():
            return self.polyline_edit.toPlainText().strip()
        if self.rb_csv.isChecked():
            if not self._trace_points:
                return ""
            return ";".join(f"{wp.lon},{wp.lat}" for wp in self._trace_points)
        # Layer source: extract coordinates from layer
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

    def _on_compute(self):
        shape = self._get_shape_string()
        if not shape:
            QMessageBox.warning(self, "Error", "No trace data provided")
            return

        costing = self.costing_combo.currentData()
        engine = self.engine_combo.currentData() or "valhalla"
        shape_match = self.shape_match_combo.currentData()
        fetch_attrs = self.attributes_check.isChecked()

        from qgis.core import QgsTask, QgsApplication

        class TraceTask(QgsTask):
            def __init__(self, desc, client, shape, costing, engine, shape_match, fetch_attrs):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._shape = shape
                self._costing = costing
                self._engine = engine
                self._shape_match = shape_match
                self._fetch_attrs = fetch_attrs
                self.response = None
                self.attr_response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    if self._engine == "osrm":
                        self.response = self._client.trace_route(self._shape, self._costing)
                    else:
                        self.response = self._client.trace_route(
                            self._shape, self._costing, shape_match=self._shape_match,
                        )
                        if self._fetch_attrs and not self.isCanceled():
                            self.attr_response = self._client.trace_attributes(
                                self._shape, self._costing, shape_match=self._shape_match,
                            )
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

        task = TraceTask(
            tr("match_loading"), client_for(engine), shape, costing, engine, shape_match, fetch_attrs,
        )
        task.taskCompleted.connect(lambda: self._on_match_done(task))
        task.taskTerminated.connect(lambda: self._on_match_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_match_done(self, task):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.match_renderer import build_matched_route_layer, build_attributes_table
                from ..core.route_renderer import build_maneuvers_layer

                build_matched_route_layer(task.response)
                build_maneuvers_layer(task.response)

                if hasattr(task, "attr_response") and task.attr_response:
                    build_attributes_table(task.attr_response)

                conf = task.response.get("confidence", None)
                if conf is not None:
                    self.iface.messageBar().pushInfo(
                        "Routing Plan", tr("match_confidence", conf=int(conf * 100)),
                    )
                else:
                    self.iface.messageBar().pushSuccess("Routing Plan", "Trace matched")
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_match_failed(task)

    def _on_match_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Match failed: {msg}")

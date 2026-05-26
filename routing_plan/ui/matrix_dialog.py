"""OD Matrix dialog — origin-destination time/distance table (F3)."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QGroupBox, QHeaderView, QFileDialog, QMessageBox,
)
from qgis.core import QgsProject, Qgis

from ..core.core import client_for
from ..core.engine import costings_for
from ..core.settings import PluginSettings
from ..i18n import tr


class MatrixDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("matrix_title"))
        self.setMinimumSize(600, 500)
        self._sources = []
        self._targets = []
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

        # Side-by-side tables: Sources | Targets
        tables_row = QHBoxLayout()

        src_group = QGroupBox(tr("matrix_sources"))
        sv = QVBoxLayout(src_group)
        self.source_table = QTableWidget(0, 3)
        self.source_table.setHorizontalHeaderLabels(["#", "Name", "Lat/Lon"])
        hdr = self.source_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.source_table.setSelectionBehavior(self.source_table.SelectionBehavior.SelectRows)
        sv.addWidget(self.source_table)
        sb = QHBoxLayout()
        self.load_src_csv_btn = QPushButton("CSV")
        sb.addWidget(self.load_src_csv_btn)
        self.load_src_layer_btn = QPushButton("Layer")
        sb.addWidget(self.load_src_layer_btn)
        self.del_src_btn = QPushButton(tr("matrix_delete_selected"))
        sb.addWidget(self.del_src_btn)
        self.clear_src_btn = QPushButton("Clear")
        sb.addWidget(self.clear_src_btn)
        sv.addLayout(sb)
        tables_row.addWidget(src_group)

        tgt_group = QGroupBox(tr("matrix_targets"))
        tv = QVBoxLayout(tgt_group)
        self.target_table = QTableWidget(0, 3)
        self.target_table.setHorizontalHeaderLabels(["#", "Name", "Lat/Lon"])
        tdr = self.target_table.horizontalHeader()
        tdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.target_table.setSelectionBehavior(self.target_table.SelectionBehavior.SelectRows)
        tv.addWidget(self.target_table)
        tb = QHBoxLayout()
        self.load_tgt_csv_btn = QPushButton("CSV")
        tb.addWidget(self.load_tgt_csv_btn)
        self.load_tgt_layer_btn = QPushButton("Layer")
        tb.addWidget(self.load_tgt_layer_btn)
        self.del_tgt_btn = QPushButton(tr("matrix_delete_selected"))
        tb.addWidget(self.del_tgt_btn)
        self.clear_tgt_btn = QPushButton("Clear")
        tb.addWidget(self.clear_tgt_btn)
        tv.addLayout(tb)
        tables_row.addWidget(tgt_group)

        layout.addLayout(tables_row)

        # Options
        self.draw_lines_check = QCheckBox(tr("matrix_draw_lines"))
        layout.addWidget(self.draw_lines_check)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("matrix_compute"))
        self.compute_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; padding: 8px 24px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #1557b0; }"
        )
        btn_layout.addWidget(self.compute_btn)
        self.export_btn = QPushButton(tr("matrix_export_csv"))
        btn_layout.addWidget(self.export_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_costing(self):
        self.costing_combo.clear()
        engine = self.engine_combo.currentData() or "valhalla"
        for val, label in costings_for(engine):
            self.costing_combo.addItem(label, val)

    def _connect_signals(self):
        self.engine_combo.currentIndexChanged.connect(lambda: self._populate_costing())
        self.load_src_csv_btn.clicked.connect(lambda: self._load_file(is_source=True))
        self.load_src_layer_btn.clicked.connect(lambda: self._load_from_layer(is_source=True))
        self.del_src_btn.clicked.connect(lambda: self._delete_selected(is_source=True))
        self.clear_src_btn.clicked.connect(lambda: self._clear_table(self.source_table))
        self.load_tgt_csv_btn.clicked.connect(lambda: self._load_file(is_source=False))
        self.load_tgt_layer_btn.clicked.connect(lambda: self._load_from_layer(is_source=False))
        self.del_tgt_btn.clicked.connect(lambda: self._delete_selected(is_source=False))
        self.clear_tgt_btn.clicked.connect(lambda: self._clear_table(self.target_table))
        self.compute_btn.clicked.connect(self._on_compute)
        self.export_btn.clicked.connect(self._export_csv)

    def _load_file(self, is_source=True):
        path, _ = QFileDialog.getOpenFileName(self, "Load waypoints", "", "CSV (*.csv)")
        if not path:
            return
        from ..core.waypoint_loader import load_csv
        wps = load_csv(path)
        self._set_waypoints(wps, is_source)

    def _load_from_layer(self, is_source=True):
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [lyr for lyr in layers if lyr.type() == Qgis.LayerType.Vector]
        if not vector_layers:
            QMessageBox.information(self, "Info", "No vector layer available")
            return
        names = [lyr.name() for lyr in vector_layers]
        from qgis.PyQt.QtWidgets import QInputDialog
        name, ok = QInputDialog.getItem(self, "Select", "Layer:", names, 0, False)
        if not ok:
            return
        layer = vector_layers[names.index(name)]
        from ..core.waypoint_loader import load_from_layer
        wps = load_from_layer(layer)
        self._set_waypoints(wps, is_source)

    def _set_waypoints(self, wps, is_source):
        table = self.source_table if is_source else self.target_table
        store = self._sources if is_source else self._targets
        store.clear()
        store.extend(wps)
        table.setRowCount(len(wps))
        for i, wp in enumerate(wps):
            table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            table.setItem(i, 1, QTableWidgetItem(wp.name or ""))
            table.setItem(i, 2, QTableWidgetItem(f"{wp.lat:.6f}, {wp.lon:.6f}"))

    def _clear_table(self, table):
        table.setRowCount(0)
        if table is self.source_table:
            self._sources.clear()
        else:
            self._targets.clear()

    def _delete_selected(self, is_source=True):
        """Remove the selected rows (multi-row supported) from the
        source or target list. Falls back to no-op if nothing is
        selected."""
        table = self.source_table if is_source else self.target_table
        store = self._sources if is_source else self._targets
        # Collect indices once, then delete from the bottom up so
        # earlier indices stay valid while we mutate.
        rows = sorted(
            {idx.row() for idx in table.selectionModel().selectedRows()},
            reverse=True,
        )
        if not rows:
            self.iface.messageBar().pushInfo(
                "Routing Plan", tr("matrix_no_selection")
            )
            return
        for row in rows:
            table.removeRow(row)
            if 0 <= row < len(store):
                del store[row]
        # Renumber the "#" column so it stays 1..N.
        from qgis.PyQt.QtWidgets import QTableWidgetItem
        for r in range(table.rowCount()):
            table.setItem(r, 0, QTableWidgetItem(str(r + 1)))

    def _on_compute(self):
        if not self._sources:
            QMessageBox.warning(self, "Error", tr("matrix_no_sources"))
            return
        if not self._targets:
            QMessageBox.warning(self, "Error", tr("matrix_no_targets"))
            return

        costing = self.costing_combo.currentData()
        engine = self.engine_combo.currentData() or "valhalla"

        from qgis.core import QgsTask, QgsApplication

        class MatrixTask(QgsTask):
            def __init__(self, desc, client, srcs, tgts, costing, engine):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._srcs = srcs
                self._tgts = tgts
                self._costing = costing
                self._engine = engine
                self.response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    if self._engine == "osrm":
                        self.response = self._client.matrix(self._srcs, self._tgts, self._costing)
                    else:
                        self.response = self._client.matrix(self._srcs, self._tgts, self._costing)
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

        task = MatrixTask(
            tr("matrix_loading"), client_for(engine), self._sources, self._targets, costing, engine,
        )
        task.taskCompleted.connect(lambda: self._on_matrix_done(task))
        task.taskTerminated.connect(lambda: self._on_matrix_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_matrix_done(self, task):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.matrix_renderer import build_matrix_table, build_matrix_lines
                self._last_response = task.response
                build_matrix_table(task.response, self._sources, self._targets)
                if self.draw_lines_check.isChecked():
                    build_matrix_lines(task.response, self._sources, self._targets)
                self.iface.messageBar().pushSuccess("Routing Plan", "Matrix computed")
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_matrix_failed(task)

    def _on_matrix_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Matrix failed: {msg}")

    def _export_csv(self):
        if not hasattr(self, "_last_response") or not self._last_response:
            QMessageBox.information(self, "Info", "Compute a matrix first")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            from ..core.exporter import export_matrix_csv
            export_matrix_csv(self._last_response, self._sources, self._targets, path)
            QMessageBox.information(self, "Export", f"Saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

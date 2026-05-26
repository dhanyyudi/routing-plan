"""Expansion dialog — debug search-tree visualization (Valhalla-only, F5)."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QListWidget,
    QGroupBox, QListWidgetItem,
)
from qgis.PyQt.QtCore import Qt

from ..core.core import client_for
from ..core.engine import VALHALLA_COSTINGS
from ..i18n import tr


class ExpansionDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.setWindowTitle(tr("exp_title"))
        self.setMinimumSize(450, 350)
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
        self.engine_combo.setToolTip("Expansion is Valhalla-only")
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

        # Action
        self.action_combo = QComboBox()
        self.action_combo.addItem("route", "route")
        self.action_combo.addItem("isochrone", "isochrone")
        self.action_combo.addItem("sources_to_targets", "sources_to_targets")
        form.addRow(tr("exp_action"), self.action_combo)
        layout.addLayout(form)

        # Options
        self.skip_opposites_check = QCheckBox(tr("exp_skip_opposites"))
        self.skip_opposites_check.setChecked(True)
        layout.addWidget(self.skip_opposites_check)

        # Properties
        props_group = QGroupBox(tr("exp_properties_label"))
        pv = QVBoxLayout(props_group)
        self.props_list = QListWidget()
        for prop in ["duration", "distance", "cost", "edge_status"]:
            item = QListWidgetItem(prop)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.props_list.addItem(item)
        pv.addWidget(self.props_list)
        layout.addWidget(props_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.compute_btn = QPushButton(tr("exp_compute"))
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
        self.compute_btn.clicked.connect(self._on_compute)

    def _get_selected_properties(self):
        props = []
        for i in range(self.props_list.count()):
            item = self.props_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                props.append(item.text())
        return props or ["duration", "distance", "cost", "edge_status"]

    def _on_compute(self):
        costing = self.costing_combo.currentData()
        action = self.action_combo.currentData()

        # Use a Jakarta default for route/isochrone
        from ..core.waypoint_loader import Waypoint
        locs = [
            Waypoint(lat=-6.2088, lon=106.8456),
            Waypoint(lat=-6.1754, lon=106.8272),
        ]
        contours = [{"time": 15}]

        from qgis.core import QgsTask, QgsApplication

        class ExpansionTask(QgsTask):
            def __init__(self, desc, client, action, locs, costing, contours, skop, props):
                super().__init__(desc, QgsTask.Flag.CanCancel)
                self._client = client
                self._action = action
                self._locs = locs
                self._costing = costing
                self._contours = contours
                self._skop = skop
                self._props = props
                self.response = None
                self.error = None
                self.result_ok = False

            def run(self):
                if self.isCanceled():
                    return False
                try:
                    kwargs = dict(
                        action=self._action, costing=self._costing,
                        skip_opposites=self._skop,
                        expansion_properties=self._props,
                    )
                    if self._action == "route":
                        kwargs["locations"] = self._locs
                    elif self._action == "isochrone":
                        kwargs["locations"] = self._locs[:1]
                        kwargs["contours"] = self._contours
                    elif self._action == "sources_to_targets":
                        kwargs["sources"] = self._locs[:1]
                        kwargs["targets"] = self._locs[1:2]
                    self.response = self._client.expansion(**kwargs)
                    if self.isCanceled():
                        return False
                    self.result_ok = True
                    return True
                except Exception as e:
                    self.error = e
                    return False

        task = ExpansionTask(
            tr("exp_loading"), client_for("valhalla"), action, locs, costing, contours,
            self.skip_opposites_check.isChecked(), self._get_selected_properties(),
        )
        task.taskCompleted.connect(lambda: self._on_expansion_done(task))
        task.taskTerminated.connect(lambda: self._on_expansion_failed(task))
        QgsApplication.taskManager().addTask(task)

    def _on_expansion_done(self, task):
        if task.isCanceled():
            return
        if task.result_ok and task.response:
            try:
                from ..core.expansion_renderer import build_expansion_layer
                build_expansion_layer(task.response)
                self.iface.messageBar().pushSuccess("Routing Plan", "Expansion computed")
            except Exception as e:
                self.iface.messageBar().pushCritical("Routing Plan", f"Render error: {e}")
        else:
            self._on_expansion_failed(task)

    def _on_expansion_failed(self, task):
        if task.isCanceled():
            return
        err = getattr(task, "error", None)
        msg = str(err) if err else "Unknown error"
        self.iface.messageBar().pushCritical("Routing Plan", f"Expansion failed: {msg}")

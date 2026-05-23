from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QFileDialog, QMessageBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QFormLayout, QHeaderView,
    QAbstractItemView, QLineEdit, QInputDialog,
)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsMessageLog, Qgis

COSTING_MODES = [
    ("auto", "Auto"),
    ("truck", "Truck"),
    ("bus", "Bus"),
    ("taxi", "Taxi"),
    ("motor_scooter", "Motor Scooter"),
    ("motorcycle", "Motorcycle"),
    ("bicycle", "Bicycle"),
    ("pedestrian", "Pedestrian"),
]


class MainDialog(QDialog):
    def __init__(self, iface, core):
        super().__init__(iface.mainWindow())
        self.iface = iface
        self.core = core
        self.waypoints = []

        self.setWindowTitle("Routing Plan")
        self.setMinimumSize(640, 520)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Banner
        banner = QLabel(
            "⚠️ Coverage area: Indonesia. "
            "Waypoint coordinates will be sent to the Valhalla server for routing."
        )
        banner.setStyleSheet(
            "background: #fff3cd; color: #856404; padding: 8px 12px; "
            "border: 1px solid #ffc107; border-radius: 4px; font-size: 12px;"
        )
        banner.setWordWrap(True)
        layout.addWidget(banner)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_waypoints_tab(), "Waypoints")
        self.tabs.addTab(self._build_costing_tab(), "Costing")
        self.tabs.addTab(self._build_departure_tab(), "Departure")
        self.tabs.addTab(self._build_advanced_tab(), "Advanced")
        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Reset all parameters to default")
        btn_layout.addWidget(self.reset_btn)

        self.save_preset_btn = QPushButton("Save Preset…")
        self.save_preset_btn.setToolTip("Save all settings to a JSON file")
        btn_layout.addWidget(self.save_preset_btn)

        self.load_preset_btn = QPushButton("Load Preset…")
        self.load_preset_btn.setToolTip("Load settings from a JSON preset file")
        btn_layout.addWidget(self.load_preset_btn)

        self.compute_btn = QPushButton("Compute Route")
        self.compute_btn.setStyleSheet(
            "QPushButton { background: #1a73e8; color: #fff; padding: 8px 24px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #1557b0; }"
        )
        self.compute_btn.setDefault(True)
        btn_layout.addWidget(self.compute_btn)

        self.close_btn = QPushButton("Close")
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        coffee = QLabel(
            '<a href="https://tiptap.gg/dhanypedia/tip" '
            'style="color: #1973f5; text-decoration: none;">☕ Buy me a coffee</a>'
        )
        coffee.setOpenExternalLinks(True)
        coffee.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(coffee)

    # ── Tab 1: Waypoints ──────────────────────────────────────────

    def _build_waypoints_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # Top bar: load buttons
        top = QHBoxLayout()

        load_label = QLabel("Load waypoints from:")
        top.addWidget(load_label)

        self.load_csv_btn = QPushButton("CSV")
        self.load_csv_btn.setToolTip("Load waypoints from CSV file (*.csv)")
        top.addWidget(self.load_csv_btn)

        self.load_xlsx_btn = QPushButton("XLSX")
        self.load_xlsx_btn.setToolTip("Load waypoints from Excel file (*.xlsx)")
        top.addWidget(self.load_xlsx_btn)

        self.load_geojson_btn = QPushButton("GeoJSON")
        self.load_geojson_btn.setToolTip("Load waypoints from GeoJSON file (*.geojson)")
        top.addWidget(self.load_geojson_btn)

        self.load_layer_btn = QPushButton("Layer")
        self.load_layer_btn.setToolTip("Load waypoints from active QGIS layer")
        top.addWidget(self.load_layer_btn)

        top.addStretch()
        layout.addLayout(top)

        # Table
        self.waypoint_table = QTableWidget(0, 4)
        self.waypoint_table.setHorizontalHeaderLabels(["#", "Name", "Latitude", "Longitude"])
        header = self.waypoint_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.waypoint_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.waypoint_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.waypoint_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.waypoint_table)

        # Bottom: clear + move + count
        bottom = QHBoxLayout()
        self.clear_btn = QPushButton("Clear All")
        bottom.addWidget(self.clear_btn)
        bottom.addSpacing(8)
        self.move_up_btn = QPushButton("↑ Up")
        self.move_up_btn.setToolTip("Move selected waypoint up 1 row")
        self.move_up_btn.setEnabled(False)
        bottom.addWidget(self.move_up_btn)
        self.move_down_btn = QPushButton("↓ Down")
        self.move_down_btn.setToolTip("Move selected waypoint down 1 row")
        self.move_down_btn.setEnabled(False)
        bottom.addWidget(self.move_down_btn)
        bottom.addStretch()
        self.count_label = QLabel("0 waypoints")
        bottom.addWidget(self.count_label)
        layout.addLayout(bottom)

        return w

    # ── Tab 2: Costing ────────────────────────────────────────────

    def _build_costing_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()
        self.costing_combo = QComboBox()
        for val, label in COSTING_MODES:
            self.costing_combo.addItem(label, val)
        form.addRow("Costing mode:", self.costing_combo)

        self.optimized_check = QCheckBox("Optimize waypoint order (TSP)")
        self.optimized_check.setToolTip(
            "When checked, Valhalla will find the most efficient waypoint order"
        )
        form.addRow("", self.optimized_check)

        layout.addLayout(form)

        # Start / End selector + roundtrip
        routing_group = QGroupBox("Routing Order")
        rlayout = QFormLayout(routing_group)
        self.start_combo = QComboBox()
        self.start_combo.setToolTip("Select starting waypoint. Default: #1")
        rlayout.addRow("Start from:", self.start_combo)
        self.end_combo = QComboBox()
        self.end_combo.setToolTip("Select ending waypoint. Default: last")
        rlayout.addRow("End at:", self.end_combo)

        self.roundtrip_check = QCheckBox("Roundtrip (return to start)")
        self.roundtrip_check.setToolTip(
            "Circular route that returns to the first waypoint. "
            "Useful for delivery tours or scenic loops."
        )
        rlayout.addRow("", self.roundtrip_check)

        self.roundtrip_check.toggled.connect(self._on_roundtrip_toggled)
        layout.addWidget(routing_group)

        # Per-mode vehicle parameters
        self._vehicle_group = QGroupBox("Vehicle Parameters")
        vlayout = QVBoxLayout(self._vehicle_group)

        # Truck parameters
        truck_w = QWidget()
        tform = QFormLayout(truck_w)
        self.truck_height = QDoubleSpinBox()
        self.truck_height.setRange(0.0, 10.0)
        self.truck_height.setDecimals(2)
        self.truck_height.setSuffix(" m")
        self.truck_height.setValue(0.0)
        tform.addRow("Height:", self.truck_height)
        self.truck_width = QDoubleSpinBox()
        self.truck_width.setRange(0.0, 10.0)
        self.truck_width.setDecimals(2)
        self.truck_width.setSuffix(" m")
        self.truck_width.setValue(0.0)
        tform.addRow("Width:", self.truck_width)
        self.truck_length = QDoubleSpinBox()
        self.truck_length.setRange(0.0, 30.0)
        self.truck_length.setDecimals(2)
        self.truck_length.setSuffix(" m")
        self.truck_length.setValue(0.0)
        tform.addRow("Length:", self.truck_length)
        self.truck_weight = QDoubleSpinBox()
        self.truck_weight.setRange(0.0, 100.0)
        self.truck_weight.setDecimals(1)
        self.truck_weight.setSuffix(" ton")
        self.truck_weight.setValue(0.0)
        tform.addRow("Weight:", self.truck_weight)
        truck_w.hide()
        self._truck_widget = truck_w

        # Bicycle parameters
        bike_w = QWidget()
        bform = QFormLayout(bike_w)
        self.bike_type = QComboBox()
        self.bike_type.addItems(["Road", "Mountain", "Cross", "Hybrid"])
        bform.addRow("Bike type:", self.bike_type)
        self.bike_speed = QDoubleSpinBox()
        self.bike_speed.setRange(5.0, 50.0)
        self.bike_speed.setValue(25.0)
        self.bike_speed.setSuffix(" km/h")
        bform.addRow("Cycling speed:", self.bike_speed)
        bike_w.hide()
        self._bike_widget = bike_w

        # Pedestrian parameters
        ped_w = QWidget()
        pform = QFormLayout(ped_w)
        self.walk_speed = QDoubleSpinBox()
        self.walk_speed.setRange(1.0, 15.0)
        self.walk_speed.setValue(5.1)
        self.walk_speed.setSuffix(" km/h")
        pform.addRow("Walking speed:", self.walk_speed)
        ped_w.hide()
        self._ped_widget = ped_w

        # Living streets + tracks + shortest (all vehicle modes)
        all_w = QWidget()
        aform = QFormLayout(all_w)
        self.use_living_streets = QDoubleSpinBox()
        self.use_living_streets.setRange(0.0, 1.0)
        self.use_living_streets.setDecimals(1)
        self.use_living_streets.setSingleStep(0.1)
        self.use_living_streets.setValue(0.5)
        aform.addRow("Use living streets:", self.use_living_streets)
        self.use_tracks = QDoubleSpinBox()
        self.use_tracks.setRange(0.0, 1.0)
        self.use_tracks.setDecimals(1)
        self.use_tracks.setSingleStep(0.1)
        self.use_tracks.setValue(0.5)
        aform.addRow("Use tracks:", self.use_tracks)
        self.shortest = QCheckBox("Shortest path (not fastest)")
        aform.addRow("", self.shortest)
        all_w.hide()
        self._all_vehicle_widget = all_w

        vlayout.addWidget(truck_w)
        vlayout.addWidget(bike_w)
        vlayout.addWidget(ped_w)
        vlayout.addWidget(all_w)
        layout.addWidget(self._vehicle_group)

        self.costing_combo.currentIndexChanged.connect(self._on_costing_changed)
        self._on_costing_changed(0)

        # Avoid / Restrictions
        avoid_group = QGroupBox("Avoid")
        avoid_layout = QVBoxLayout(avoid_group)

        self._avoid_checkboxes = {}
        _avoidable = [
            ("motorway", "Motorway / freeway"),
            ("trunk",    "Trunk / national road"),
            ("toll",     "Toll road (toll=yes)"),
            ("ferry",    "Ferry"),
            ("track",    "Track / unpaved road"),
            ("living_street", "Living street"),
        ]
        for key, label in _avoidable:
            cb = QCheckBox(label)
            cb.setToolTip(f"OSM highway={key}" if key not in ("toll", "ferry") else f"OSM {key}=yes")
            self._avoid_checkboxes[key] = cb
            avoid_layout.addWidget(cb)

        layout.addWidget(avoid_group)

        layout.addStretch()
        return w

    def _on_costing_changed(self, index):
        mode = self.costing_combo.itemData(index)
        self._truck_widget.setVisible(mode == "truck")
        self._bike_widget.setVisible(mode == "bicycle")
        self._ped_widget.setVisible(mode == "pedestrian")
        self._all_vehicle_widget.setVisible(mode not in ("bicycle", "pedestrian"))

    def _on_date_type_changed(self, index):
        data = self.date_type_combo.currentData()
        visible = data in (1, 2, 3)
        self.date_time_edit.setVisible(visible)
        if hasattr(self, "_date_time_label") and self._date_time_label:
            self._date_time_label.setVisible(visible)

    # ── Tab 3: Departure ─────────────────────────────────────────

    def _build_departure_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()

        from qgis.PyQt.QtCore import QDateTime
        from qgis.PyQt.QtWidgets import QDateTimeEdit

        self.date_type_combo = QComboBox()
        self.date_type_combo.addItem("Now (no time constraint)", 0)
        self.date_type_combo.addItem("Depart at…", 1)
        self.date_type_combo.addItem("Arrive by…", 2)
        self.date_type_combo.addItem("Invariant (time-independent)", 3)
        form.addRow("Date/time type:", self.date_type_combo)

        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.date_time_edit.setCalendarPopup(True)
        self.date_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_time_edit.setMinimumDateTime(QDateTime.currentDateTime().addSecs(-86400 * 365))
        self.date_time_edit.setVisible(False)
        self._date_time_label = QLabel("Date/time:")
        form.addRow(self._date_time_label, self.date_time_edit)
        self._date_time_label.setVisible(False)

        self.alternates_spin = QSpinBox()
        self.alternates_spin.setRange(0, 3)
        self.alternates_spin.setToolTip("Number of alternate routes (0-3)")
        form.addRow("Alternates:", self.alternates_spin)

        layout.addLayout(form)

        self.units_combo = QComboBox()
        self.units_combo.addItem("Kilometers", "kilometers")
        self.units_combo.addItem("Miles", "miles")
        form.addRow("Units:", self.units_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Bahasa Indonesia", "id")
        from ..core.settings import PluginSettings
        lang = PluginSettings.get_language()
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        form.addRow("Instruction language:", self.lang_combo)

        layout.addStretch()
        return w

    # ── Tab 4: Advanced ──────────────────────────────────────────

    def _build_advanced_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()

        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setText(self.core.client.endpoint)
        form.addRow("Endpoint URL:", self.endpoint_edit)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSuffix(" sec")
        form.addRow("Timeout:", self.timeout_spin)

        self.debug_raw_check = QCheckBox(
            "Show response JSON in dialog after compute"
        )
        form.addRow("", self.debug_raw_check)

        self.debug_log_check = QCheckBox(
            "Log raw payload to QGIS log"
        )
        form.addRow("", self.debug_log_check)

        layout.addLayout(form)

        info = QLabel(
            "↗ Endpoint and timeout can also be changed via Settings…"
        )
        info.setStyleSheet("color: #5f6368; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()
        return w

    # ── Tab: Options (LEGACY — content moved to Departure + Advanced) ──

    def _build_options_tab(self):
        pass

    # ── Signals ───────────────────────────────────────────────────

    def _connect_signals(self):
        self.load_csv_btn.clicked.connect(lambda: self._load_file("CSV (*.csv)"))
        self.load_xlsx_btn.clicked.connect(lambda: self._load_file("Excel (*.xlsx)"))
        self.load_geojson_btn.clicked.connect(lambda: self._load_file("GeoJSON (*.geojson)"))
        self.load_layer_btn.clicked.connect(self._load_from_layer)
        self.clear_btn.clicked.connect(self._clear_waypoints)
        self.compute_btn.clicked.connect(self._on_compute)
        self.close_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self._reset)
        self.save_preset_btn.clicked.connect(self._save_preset)
        self.load_preset_btn.clicked.connect(self._load_preset)
        self.date_type_combo.currentIndexChanged.connect(self._on_date_type_changed)
        self.move_up_btn.clicked.connect(lambda: self._move_waypoint(-1))
        self.move_down_btn.clicked.connect(lambda: self._move_waypoint(+1))
        self.waypoint_table.itemSelectionChanged.connect(self._update_move_buttons_state)

    def _load_file(self, file_filter):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load waypoints", "", file_filter,
        )
        if not path:
            return

        try:
            from ..core.waypoint_loader import (
                load_csv, load_xlsx, load_geojson,
            )
            ext = path.lower()
            if ext.endswith(".csv"):
                wps = load_csv(path)
            elif ext.endswith(".xlsx"):
                wps = load_xlsx(path)
            elif ext.endswith(".geojson"):
                wps = load_geojson(path)
            else:
                QMessageBox.warning(self, "Error", f"Unsupported format: {path}")
                return

            self._set_waypoints(wps)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    def _load_from_layer(self):
        layers = QgsProject.instance().mapLayers().values()
        vector_layers = [
            l for l in layers
            if l.type() == Qgis.LayerType.Vector
        ]
        if not vector_layers:
            QMessageBox.information(
                self, "Info",
                "No active vector layer in project.\n"
                "Add a point layer (CSV, GeoJSON, etc.) first."
            )
            return

        items = [l.name() for l in vector_layers]
        from qgis.PyQt.QtWidgets import QInputDialog
        name, ok = QInputDialog.getItem(
            self, "Select Layer", "Layer:", items, 0, False,
        )
        if not ok:
            return

        layer = vector_layers[items.index(name)]
        try:
            from ..core.waypoint_loader import load_from_layer
            wps = load_from_layer(layer)
            self._set_waypoints(wps)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load layer:\n{e}")

    def _set_waypoints(self, waypoints):
        from qgis.PyQt.QtGui import QBrush, QColor
        INVALID_BG = QBrush(QColor("#fce8e6"))

        self.waypoints = waypoints
        self.waypoint_table.setRowCount(len(waypoints))
        invalid_rows = []

        for i, wp in enumerate(waypoints):
            errors = wp.validate()
            is_invalid = bool(errors)
            if is_invalid:
                invalid_rows.append((i + 1, errors))

            items = [
                QTableWidgetItem(str(i + 1)),
                QTableWidgetItem(wp.name or ""),
                QTableWidgetItem(str(wp.lat)),
                QTableWidgetItem(str(wp.lon)),
            ]
            for col, item in enumerate(items):
                if is_invalid:
                    item.setBackground(INVALID_BG)
                    item.setToolTip("\n".join(errors))
                self.waypoint_table.setItem(i, col, item)

        self.count_label.setText(f"{len(waypoints)} waypoints")
        self._update_compute_button_state(invalid_rows)
        self._refresh_start_end_combos()

    def _refresh_start_end_combos(self):
        prev_start = self.start_combo.currentData() if self.start_combo.count() else None
        prev_end = self.end_combo.currentData() if self.end_combo.count() else None
        self.start_combo.blockSignals(True)
        self.end_combo.blockSignals(True)
        self.start_combo.clear()
        self.end_combo.clear()
        for i, wp in enumerate(self.waypoints):
            label = f"#{i + 1} — {wp.name or '(no name)'}"
            self.start_combo.addItem(label, i)
            self.end_combo.addItem(label, i)
        if self.waypoints:
            si = prev_start if prev_start is not None and prev_start < len(self.waypoints) else 0
            ei = prev_end if prev_end is not None and prev_end < len(self.waypoints) else len(self.waypoints) - 1
            self.start_combo.setCurrentIndex(si)
            self.end_combo.setCurrentIndex(ei)
        self.start_combo.blockSignals(False)
        self.end_combo.blockSignals(False)

    def _on_roundtrip_toggled(self, checked):
        self.end_combo.setEnabled(not checked)
        if checked:
            self.end_combo.setToolTip("End point = start point (roundtrip active)")
        else:
            self.end_combo.setToolTip("Select ending waypoint. Default: last")

    def _update_compute_button_state(self, invalid_rows):
        if invalid_rows:
            self.compute_btn.setEnabled(False)
            sample = invalid_rows[0]
            self.compute_btn.setToolTip(
                f"⚠️ {len(invalid_rows)} waypoint(s) with invalid coordinates. "
                f"Check row #{sample[0]} (hover for detail). "
                f"Fix or clear before compute."
            )
        else:
            self.compute_btn.setEnabled(True)
            self.compute_btn.setToolTip("Compute route between waypoints")

    def _clear_waypoints(self):
        self.waypoints = []
        self.waypoint_table.setRowCount(0)
        self.count_label.setText("0 waypoints")
        self._update_compute_button_state([])

    def _get_waypoints_in_order(self):
        from ..core.waypoint_loader import Waypoint
        wps = []
        for row in range(self.waypoint_table.rowCount()):
            lat_item = self.waypoint_table.item(row, 2)
            lon_item = self.waypoint_table.item(row, 3)
            if not (lat_item and lon_item):
                continue
            try:
                lat = float(lat_item.text())
                lon = float(lon_item.text())
            except ValueError:
                continue
            name_item = self.waypoint_table.item(row, 1)
            name = name_item.text() if name_item else None
            wps.append(Waypoint(lat=lat, lon=lon, name=name))
        return wps

    def _renumber_waypoints(self):
        for row in range(self.waypoint_table.rowCount()):
            self.waypoint_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

    def _update_move_buttons_state(self):
        rows = sorted({i.row() for i in self.waypoint_table.selectedIndexes()})
        if not rows:
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            return
        row = rows[0]
        self.move_up_btn.setEnabled(row > 0)
        self.move_down_btn.setEnabled(row < self.waypoint_table.rowCount() - 1)

    def _move_waypoint(self, delta):
        rows = sorted({i.row() for i in self.waypoint_table.selectedIndexes()})
        if not rows:
            return
        row = rows[0]
        new_row = row + delta
        if not (0 <= new_row < self.waypoint_table.rowCount()):
            return
        self.waypoints[row], self.waypoints[new_row] = (
            self.waypoints[new_row], self.waypoints[row],
        )
        self._set_waypoints(self.waypoints)
        self.waypoint_table.selectRow(new_row)

    _INDONESIA_BBOX = {
        "lat_min": -11.5, "lat_max": 6.5,
        "lon_min": 94.5, "lon_max": 141.5,
    }

    def _is_in_indonesia(self, wp):
        return (
            self._INDONESIA_BBOX["lat_min"] <= wp.lat <= self._INDONESIA_BBOX["lat_max"]
            and self._INDONESIA_BBOX["lon_min"] <= wp.lon <= self._INDONESIA_BBOX["lon_max"]
        )

    def _on_compute(self):
        waypoints = self._get_waypoints_in_order()
        if len(waypoints) < 2:
            QMessageBox.warning(
                self, "Not Enough Waypoints",
                "At least 2 waypoints required to compute a route.\n"
                "Currently: {} waypoint(s).".format(len(waypoints)),
            )
            return

        # Bbox Indonesia pre-flight validation
        outside = [
            (i + 1, wp.name or f"WP {i + 1}")
            for i, wp in enumerate(waypoints)
            if not self._is_in_indonesia(wp)
        ]
        if outside:
            listing = "\n".join(f"  #{idx}: {name}" for idx, name in outside[:10])
            if len(outside) > 10:
                listing += f"\n  ... dan {len(outside) - 10} lainnya"
            reply = QMessageBox.question(
                self, "Waypoint Outside Indonesia",
                f"The following waypoints are outside Indonesia:\n\n{listing}\n\n"
                f"Current Valhalla coverage is Indonesia only. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.tabs.setCurrentIndex(0)
                self.waypoint_table.selectRow(outside[0][0] - 1)
                return

        # Reorder by Start/End selection
        start_idx = self.start_combo.currentData() or 0
        end_idx = self.end_combo.currentData() or (len(waypoints) - 1)

        if not self.roundtrip_check.isChecked():
            if start_idx == end_idx:
                QMessageBox.warning(
                    self, "Start Equals End",
                    "Start and End point are the same. Check Roundtrip if you want "
                    "a route returning to start, or choose a different End."
                )
                return
            middle = [waypoints[i] for i in range(len(waypoints))
                      if i != start_idx and i != end_idx]
            waypoints = [waypoints[start_idx]] + middle + [waypoints[end_idx]]
        else:
            from dataclasses import replace
            middle = [waypoints[i] for i in range(len(waypoints)) if i != start_idx]
            waypoints = [waypoints[start_idx]] + middle + [replace(waypoints[start_idx])]

        costing = self.costing_combo.currentData()
        optimized = self.optimized_check.isChecked()

        costing_options = None
        mode_opts = {}

        # Avoid highway classes — map ke Valhalla costing_options
        avoid_selected = {k for k, cb in self._avoid_checkboxes.items() if cb.isChecked()}
        if "motorway" in avoid_selected or "trunk" in avoid_selected:
            mode_opts["use_highways"] = 0.0
        if "toll" in avoid_selected:
            mode_opts["use_tolls"] = 0.0
        if "ferry" in avoid_selected:
            mode_opts["use_ferry"] = 0.0
        if "track" in avoid_selected:
            mode_opts["use_tracks"] = 0.0
        if "living_street" in avoid_selected:
            mode_opts["use_living_streets"] = 0.0

        # Per-mode vehicle parameters
        if costing == "truck":
            for attr, key in [
                ("truck_height", "height"), ("truck_width", "width"),
                ("truck_length", "length"), ("truck_weight", "weight"),
            ]:
                val = getattr(self, attr).value()
                if val > 0:
                    mode_opts[key] = val
        elif costing == "bicycle":
            mode_opts["bicycle_type"] = self.bike_type.currentText()
            mode_opts["cycling_speed"] = self.bike_speed.value()
        elif costing == "pedestrian":
            mode_opts["walking_speed"] = self.walk_speed.value()

        # Common vehicle params
        if costing not in ("bicycle", "pedestrian"):
            mode_opts["use_living_streets"] = self.use_living_streets.value()
            mode_opts["use_tracks"] = self.use_tracks.value()
            if self.shortest.isChecked():
                mode_opts["shortest"] = True

        if mode_opts:
            costing_options = {costing: mode_opts}

        directions_options = {
            "units": self.units_combo.currentData(),
            "language": self.lang_combo.currentData(),
        }

        date_type = self.date_type_combo.currentData()
        date_time = None
        if date_type != 0:
            iso = self.date_time_edit.dateTime().toString("yyyy-MM-ddTHH:mm")
            date_time = {"type": date_type, "value": iso}

        self.core.compute_route(
            waypoints,
            costing=costing,
            costing_options=costing_options,
            directions_options=directions_options,
            optimized=optimized,
            date_time=date_time,
        )

        self.accept()

    def _reset(self):
        self._clear_waypoints()
        self.costing_combo.setCurrentIndex(0)
        self.optimized_check.setChecked(False)
        self.roundtrip_check.setChecked(False)
        self._refresh_start_end_combos()
        for cb in self._avoid_checkboxes.values():
            cb.setChecked(False)
        self.truck_height.setValue(0.0)
        self.truck_width.setValue(0.0)
        self.truck_length.setValue(0.0)
        self.truck_weight.setValue(0.0)
        self.bike_speed.setValue(25.0)
        self.walk_speed.setValue(5.1)
        self.use_living_streets.setValue(0.5)
        self.use_tracks.setValue(0.5)
        self.shortest.setChecked(False)
        self.alternates_spin.setValue(0)
        self.units_combo.setCurrentIndex(0)
        self.lang_combo.setCurrentIndex(0)
        from ..core.settings import PluginSettings
        lang = PluginSettings.get_language()
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.endpoint_edit.setText(self.core.client.endpoint)
        self.timeout_spin.setValue(60)
        self.debug_raw_check.setChecked(False)
        self.debug_log_check.setChecked(False)
        from qgis.PyQt.QtCore import QDateTime
        self.date_type_combo.setCurrentIndex(0)
        self.date_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))

    def _save_preset(self):
        import json
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", "", "JSON (*.json)",
        )
        if not path:
            return
        preset = {
            "costing": self.costing_combo.currentData(),
            "optimized": self.optimized_check.isChecked(),
            "roundtrip": self.roundtrip_check.isChecked(),
            "avoid": {k: cb.isChecked() for k, cb in self._avoid_checkboxes.items()},
            "truck_height": self.truck_height.value(),
            "truck_width": self.truck_width.value(),
            "truck_length": self.truck_length.value(),
            "truck_weight": self.truck_weight.value(),
            "bike_speed": self.bike_speed.value(),
            "walk_speed": self.walk_speed.value(),
            "use_living_streets": self.use_living_streets.value(),
            "use_tracks": self.use_tracks.value(),
            "shortest": self.shortest.isChecked(),
            "alternates": self.alternates_spin.value(),
            "units": self.units_combo.currentData(),
            "language": self.lang_combo.currentData(),
            "date_type": self.date_type_combo.currentData(),
        }
        with open(path, "w") as f:
            json.dump(preset, f, indent=2)
        QMessageBox.information(self, "Preset", f"Preset saved: {path}")

    def _load_preset(self):
        import json
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Preset", "", "JSON (*.json)",
        )
        if not path:
            return
        try:
            with open(path) as f:
                preset = json.load(f)
            idx = self.costing_combo.findData(preset.get("costing", "auto"))
            if idx >= 0:
                self.costing_combo.setCurrentIndex(idx)
            self.optimized_check.setChecked(preset.get("optimized", False))
            self.roundtrip_check.setChecked(preset.get("roundtrip", False))
            avoid = preset.get("avoid", {})
            for k, cb in self._avoid_checkboxes.items():
                cb.setChecked(avoid.get(k, False))
            self.truck_height.setValue(preset.get("truck_height", 0.0))
            self.truck_width.setValue(preset.get("truck_width", 0.0))
            self.truck_length.setValue(preset.get("truck_length", 0.0))
            self.truck_weight.setValue(preset.get("truck_weight", 0.0))
            self.bike_speed.setValue(preset.get("bike_speed", 25.0))
            self.walk_speed.setValue(preset.get("walk_speed", 5.1))
            self.use_living_streets.setValue(preset.get("use_living_streets", 0.5))
            self.use_tracks.setValue(preset.get("use_tracks", 0.5))
            self.shortest.setChecked(preset.get("shortest", False))
            self.alternates_spin.setValue(preset.get("alternates", 0))
            idx = self.units_combo.findData(preset.get("units", "kilometers"))
            if idx >= 0:
                self.units_combo.setCurrentIndex(idx)
            idx = self.lang_combo.findData(preset.get("language", "id"))
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
            dt = preset.get("date_type", 0)
            idx = self.date_type_combo.findData(dt)
            if idx >= 0:
                self.date_type_combo.setCurrentIndex(idx)
            QMessageBox.information(self, "Preset", f"Preset loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset:\n{e}")

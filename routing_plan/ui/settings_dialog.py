from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton,
    QDialogButtonBox, QCheckBox,
)

from ..core.settings import PluginSettings
from ..i18n import tr

COSTING_OPTIONS = [
    ("auto", "Auto"),
    ("truck", "Truck"),
    ("bus", "Bus"),
    ("taxi", "Taxi"),
    ("motor_scooter", "Motor Scooter"),
    ("motorcycle", "Motorcycle"),
    ("bicycle", "Bicycle"),
    ("pedestrian", "Pedestrian"),
]

ENGINE_OPTIONS = [
    ("valhalla", "Valhalla"),
    ("osrm", "OSRM"),
]

LANGUAGE_OPTIONS = [
    ("en", "English"),
    ("id", "Bahasa Indonesia"),
]

UNITS_OPTIONS = [
    ("kilometers", "Kilometers"),
    ("miles", "Miles"),
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.engine_combo = QComboBox()
        for val, label in ENGINE_OPTIONS:
            self.engine_combo.addItem(label, val)
        form.addRow(tr("engine_label"), self.engine_combo)

        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setPlaceholderText("https://valhalla.dhanypedia.it.com")
        form.addRow(tr("endpoint_url"), self.endpoint_edit)

        self.osrm_endpoint_edit = QLineEdit()
        self.osrm_endpoint_edit.setPlaceholderText("https://router.project-osrm.org")
        form.addRow("OSRM Endpoint URL:", self.osrm_endpoint_edit)

        self.costing_combo = QComboBox()
        for val, label in COSTING_OPTIONS:
            self.costing_combo.addItem(label, val)
        form.addRow(tr("default_costing"), self.costing_combo)

        self.language_combo = QComboBox()
        for val, label in LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, val)
        form.addRow(tr("language"), self.language_combo)

        self.units_combo = QComboBox()
        for val, label in UNITS_OPTIONS:
            self.units_combo.addItem(label, val)
        form.addRow(tr("units"), self.units_combo)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(tr("seconds_suffix"))
        form.addRow(tr("timeout"), self.timeout_spin)

        self.auto_clear_check = QCheckBox()
        form.addRow(tr("auto_clear_previous"), self.auto_clear_check)

        info = QLabel(tr("privacy_notice"))
        info.setWordWrap(True)
        info.setStyleSheet("color: #5f6368; font-size: 12px;")
        layout.addWidget(info)

        layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton(tr("reset_default"))
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        btn_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)

        layout.addLayout(btn_layout)

    def _load_settings(self):
        s = PluginSettings
        engine = s.get_engine()
        idx = self.engine_combo.findData(engine)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)

        self.endpoint_edit.setText(s.get_endpoint_for("valhalla"))
        self.osrm_endpoint_edit.setText(s.get_endpoint_for("osrm"))

        idx = self.costing_combo.findData(s.get_default_costing())
        if idx >= 0:
            self.costing_combo.setCurrentIndex(idx)

        idx = self.language_combo.findData(s.get_language())
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

        idx = self.units_combo.findData(s.get_units())
        if idx >= 0:
            self.units_combo.setCurrentIndex(idx)

        self.timeout_spin.setValue(s.get_timeout())
        self.auto_clear_check.setChecked(s.get_auto_clear_previous())

    def _accept(self):
        s = PluginSettings
        s.set_engine(self.engine_combo.currentData())
        s.set_endpoint_for("valhalla", self.endpoint_edit.text().strip())
        s.set_endpoint_for("osrm", self.osrm_endpoint_edit.text().strip())
        s.set_default_costing(self.costing_combo.currentData())
        s.set_language(self.language_combo.currentData())
        s.set_units(self.units_combo.currentData())
        s.set_timeout(self.timeout_spin.value())
        s.set_auto_clear_previous(self.auto_clear_check.isChecked())
        self.accept()

    def _reset(self):
        PluginSettings.reset_all()
        self._load_settings()
        self.engine_combo.setCurrentIndex(0)

import os

from qgis.PyQt.QtCore import Qt, QSize, QRect
from qgis.PyQt.QtGui import QIcon, QPainter, QFont, QPalette
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QStyle

from ..core.maneuver_formatter import (
    format_distance,
    format_total_summary,
    icon_path_for_maneuver_type,
    unicode_for_maneuver_type,
    translate_instruction,
)


class DirectionItemDelegate(QStyledItemDelegate):
    """Google Maps-style item rendering for directions dock.

    Layout per item:
        [ICON 28px]  Turn left onto Jl. Sudirman
                      819 m
    """
    PADDING = 12
    ICON_SIZE = 28
    ITEM_HEIGHT = 60
    INSTRUCTION_PT = 13
    DISTANCE_PT = 10

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.color(QPalette.ColorRole.HighlightedText)
            muted_color = text_color
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, option.palette.alternateBase())
            text_color = option.palette.color(QPalette.ColorRole.Text)
            muted_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        else:
            text_color = option.palette.color(QPalette.ColorRole.Text)
            muted_color = option.palette.color(QPalette.ColorRole.PlaceholderText)

        # Subtle bottom border
        painter.setPen(option.palette.color(QPalette.ColorRole.Mid))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        # Icon
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_rect = QRect(
            option.rect.left() + self.PADDING,
            option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2,
            self.ICON_SIZE, self.ICON_SIZE,
        )
        if icon and not icon.isNull():
            self._tinted_icon(icon, text_color).paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

        # Text area
        text_left = option.rect.left() + self.PADDING + self.ICON_SIZE + self.PADDING
        text_width = option.rect.right() - self.PADDING - text_left

        instruction = index.data(Qt.ItemDataRole.UserRole + 1) or ""
        distance = index.data(Qt.ItemDataRole.UserRole + 2) or ""

        center_y = option.rect.center().y()
        line_gap = 2

        # Instruction (regular, 13pt)
        instr_font = QFont(option.font)
        instr_font.setPointSize(self.INSTRUCTION_PT)
        painter.setFont(instr_font)
        painter.setPen(text_color)
        instr_height = painter.fontMetrics().height()
        instr_rect = QRect(text_left, center_y - instr_height - line_gap // 2, text_width, instr_height)
        elided = painter.fontMetrics().elidedText(instruction, Qt.TextElideMode.ElideRight, text_width)
        painter.drawText(instr_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        # Distance (bold, 10pt, muted)
        if distance:
            dist_font = QFont(option.font)
            dist_font.setPointSize(self.DISTANCE_PT)
            dist_font.setBold(True)
            painter.setFont(dist_font)
            painter.setPen(muted_color)
            dist_height = painter.fontMetrics().height()
            dist_rect = QRect(text_left, center_y + line_gap // 2, text_width, dist_height)
            painter.drawText(dist_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, distance)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(0, self.ITEM_HEIGHT)

    def _tinted_icon(self, icon, color):
        from qgis.PyQt.QtGui import QPixmap, QImage
        pixmap = icon.pixmap(self.ICON_SIZE, self.ICON_SIZE)
        if pixmap.isNull():
            return icon
        image = pixmap.toImage()
        tinted = QImage(image.size(), QImage.Format.Format_ARGB32)
        tinted.fill(Qt.GlobalColor.transparent)
        tp = QPainter(tinted)
        tp.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        tp.drawImage(0, 0, image)
        tp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        tp.fillRect(tinted.rect(), color)
        tp.end()
        return QIcon(QPixmap.fromImage(tinted))


class DirectionsDock:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))
        self.dock_widget = None
        self.list_widget = None
        self.header_label = None
        self.subheader_label = None
        self.export_html_btn = None
        self.export_geojson_btn = None
        self.export_kml_btn = None
        self.export_gpkg_btn = None
        self._maneuver_data = []
        self._last_response = None
        self._route_layer = None
        self._maneuvers_layer = None

    def show(self, response, route_layer=None, maneuvers_layer=None, lang="en"):
        from qgis.PyQt.QtCore import Qt

        self._last_response = response
        self._route_layer = route_layer
        self._maneuvers_layer = maneuvers_layer
        self._lang = lang

        if self.dock_widget is None:
            self._build_ui()

        self._populate(response)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.show()
        self.dock_widget.raise_()

    def hide(self):
        if self.dock_widget:
            self.dock_widget.hide()

    def _build_ui(self):
        from qgis.PyQt.QtGui import QFont
        from qgis.PyQt.QtWidgets import (
            QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QPushButton, QListWidget,
        )

        self.dock_widget = QDockWidget("Directions", self.iface.mainWindow())
        self.dock_widget.setObjectName("RoutingPlanDirectionsDock")
        self.dock_widget.setMinimumWidth(240)
        self.dock_widget.resize(280, 600)

        main_widget = QWidget()
        main_widget.setStyleSheet("background: palette(window); color: palette(window-text);")
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.header_label = QLabel()
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.header_label.setFont(font)
        self.header_label.setWordWrap(True)

        self.subheader_label = QLabel()
        self.subheader_label.setStyleSheet("color: palette(placeholder-text); font-size: 12px;")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.export_html_btn = QPushButton("HTML")
        self.export_html_btn.setToolTip("Export directions to HTML file with interactive map")
        self.export_html_btn.clicked.connect(self._on_export_html)

        self.export_geojson_btn = QPushButton("GeoJSON")
        self.export_geojson_btn.setToolTip("Export route + maneuvers to GeoJSON")
        self.export_geojson_btn.clicked.connect(self._on_export_geojson)

        self.export_kml_btn = QPushButton("KML")
        self.export_kml_btn.setToolTip("Export route + maneuvers to KML")
        self.export_kml_btn.clicked.connect(self._on_export_kml)

        self.export_gpkg_btn = QPushButton("GPKG")
        self.export_gpkg_btn.setToolTip("Save route + maneuvers layers to GeoPackage")
        self.export_gpkg_btn.clicked.connect(self._on_export_gpkg)

        self.archive_btn = QPushButton("📌 Archive")
        self.archive_btn.setToolTip(
            "Save current route as permanent named group.\n"
            "Next Compute Route will create a fresh group, current route preserved."
        )
        self.archive_btn.clicked.connect(self._on_archive)

        self.clear_route_btn = QPushButton("🗑 Clear")
        self.clear_route_btn.setToolTip("Remove current route from canvas and hide dock")
        self.clear_route_btn.clicked.connect(self._on_clear_route)

        for btn in [self.export_html_btn, self.export_geojson_btn, self.export_kml_btn,
                    self.export_gpkg_btn, self.archive_btn, self.clear_route_btn]:
            btn.setMaximumHeight(28)
            btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")

        btn_layout.addWidget(self.export_html_btn)
        btn_layout.addWidget(self.export_geojson_btn)
        btn_layout.addWidget(self.export_kml_btn)
        btn_layout.addWidget(self.export_gpkg_btn)
        btn_layout.addSpacing(8)
        btn_layout.addWidget(self.archive_btn)
        btn_layout.addWidget(self.clear_route_btn)
        btn_layout.addStretch()

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setItemDelegate(DirectionItemDelegate(self.list_widget))
        self.list_widget.setIconSize(QSize(DirectionItemDelegate.ICON_SIZE, DirectionItemDelegate.ICON_SIZE))
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid palette(mid);
                border-radius: 4px;
                background: palette(base);
                color: palette(text);
            }
            QListWidget::item {
                padding: 8px 4px;
                border-bottom: 1px solid palette(midlight);
                color: palette(text);
            }
            QListWidget::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
            QListWidget::item:hover {
                background: palette(alternate-base);
                color: palette(text);
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.header_label)
        layout.addWidget(self.subheader_label)
        layout.addLayout(btn_layout)
        layout.addWidget(self.list_widget)

        self.dock_widget.setWidget(main_widget)

    def _populate(self, response):
        summary = format_total_summary(response)
        self.header_label.setText(
            f"{summary['distance']} · {summary['duration']}"
        )

        leg_count = len(response.get("trip", {}).get("legs", []))
        waypoint_count = len(response.get("trip", {}).get("locations", []))
        self.subheader_label.setText(
            f"{waypoint_count} titik · {leg_count} segmen · "
            f"{summary['length_km']} km · {summary['time_min']} menit"
        )

        self._maneuver_data = []
        self.list_widget.clear()

        from ..core.route_renderer import decode_polyline6
        from qgis.PyQt.QtWidgets import QListWidgetItem

        for leg in response.get("trip", {}).get("legs", []):
            shape_str = leg.get("shape", "")
            coords = decode_polyline6(shape_str)
            for m in leg.get("maneuvers", []):
                icon_path = icon_path_for_maneuver_type(m.get("type", 0))
                instruction = m.get("instruction", "")
                instruction = translate_instruction(instruction, self._lang)
                length_m = m.get("length", 0)
                if response.get("trip", {}).get("units") == "miles":
                    length_m = length_m * 1609.34
                else:
                    length_m = length_m * 1000
                dist_text = format_distance(length_m) if length_m > 0 else ""

                item = QListWidgetItem()
                if icon_path:
                    item.setIcon(QIcon(icon_path))
                else:
                    unicode_icon = unicode_for_maneuver_type(m.get("type", 0))
                    item.setText(f"{unicode_icon}  {instruction}")

                item.setData(Qt.ItemDataRole.UserRole + 1, instruction)
                item.setData(Qt.ItemDataRole.UserRole + 2, dist_text)
                item.setToolTip(f"{instruction}\n{dist_text}" if dist_text else instruction)

                self.list_widget.addItem(item)

                begin_idx = m.get("begin_shape_index", 0)
                if begin_idx < len(coords):
                    lat, lon = coords[begin_idx]
                elif coords:
                    lat, lon = coords[0]
                else:
                    lat, lon = None, None

                self._maneuver_data.append({
                    "lat": lat,
                    "lon": lon,
                    "instruction": instruction,
                    "distance": dist_text,
                })

    def _on_item_clicked(self, item):
        idx = self.list_widget.row(item)
        if not (0 <= idx < len(self._maneuver_data)):
            return
        data = self._maneuver_data[idx]
        if data["lat"] is None or data["lon"] is None:
            return

        from qgis.core import (
            QgsPointXY, QgsCoordinateTransform,
            QgsCoordinateReferenceSystem, QgsProject,
        )
        canvas = self.iface.mapCanvas()
        src_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        dst_crs = canvas.mapSettings().destinationCrs()

        point = QgsPointXY(data["lon"], data["lat"])
        if src_crs != dst_crs:
            transform = QgsCoordinateTransform(src_crs, dst_crs, QgsProject.instance())
            point = transform.transform(point)

        canvas.setCenter(point)
        canvas.zoomScale(5000)
        canvas.refresh()

    def _on_export_html(self):
        from ..i18n import tr
        if not self._last_response:
            return
        path = self._save_dialog(tr("html_filter"))
        if not path:
            return
        try:
            from ..core.exporter import export_html
            template_path = os.path.join(self.plugin_dir, "templates", "directions.html")
            export_html(self._last_response, path, template_path)
            self.iface.messageBar().pushSuccess("Routing Plan", tr("html_saved", path=path))
        except Exception as e:
            self.iface.messageBar().pushCritical("Routing Plan", tr("export_html_failed", error=str(e)))

    def _on_export_geojson(self):
        from ..i18n import tr
        if not self._last_response:
            return
        path = self._save_dialog(tr("geojson_filter"))
        if not path:
            return
        try:
            from ..core.exporter import export_geojson
            export_geojson(self._last_response, path)
            self.iface.messageBar().pushSuccess("Routing Plan", tr("geojson_saved", path=path))
        except Exception as e:
            self.iface.messageBar().pushCritical("Routing Plan", tr("export_geojson_failed", error=str(e)))

    def _on_export_kml(self):
        from ..i18n import tr
        if not self._last_response:
            return
        path = self._save_dialog(tr("kml_filter"))
        if not path:
            return
        try:
            from ..core.exporter import export_kml
            export_kml(self._last_response, path)
            self.iface.messageBar().pushSuccess("Routing Plan", tr("kml_saved", path=path))
        except Exception as e:
            self.iface.messageBar().pushCritical("Routing Plan", tr("export_kml_failed", error=str(e)))

    def _on_export_gpkg(self):
        from ..i18n import tr
        if not self._route_layer or not self._maneuvers_layer:
            self.iface.messageBar().pushWarning("Routing Plan", tr("layer_not_available"))
            return
        path = self._save_dialog(tr("gpkg_filter"))
        if not path:
            return
        try:
            from ..core.exporter import export_geopackage
            export_geopackage(self._route_layer, self._maneuvers_layer, path)
            self.iface.messageBar().pushSuccess("Routing Plan", tr("gpkg_saved", path=path))
        except Exception as e:
            self.iface.messageBar().pushCritical("Routing Plan", tr("export_gpkg_failed", error=str(e)))

    def _save_dialog(self, file_filter):
        from ..i18n import tr
        from qgis.PyQt.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self.dock_widget,
            tr("save_as"),
            "",
            file_filter,
        )
        return path if path else None

    def _on_archive(self):
        from qgis.core import QgsProject
        from datetime import datetime
        from qgis.PyQt.QtWidgets import QInputDialog

        project = QgsProject.instance()
        root = project.layerTreeRoot()
        group = root.findGroup("Routing Plan")
        if group is None:
            self.iface.messageBar().pushWarning(
                "Routing Plan",
                "No route to archive. Compute a route first.",
            )
            return

        default_label = ""
        if self._last_response:
            locs = self._last_response.get("trip", {}).get("locations", [])
            if locs and locs[0].get("name"):
                default_label = locs[0]["name"][:20]

        timestamp = datetime.now().strftime("%H:%M")
        suggested = f"Routing Plan — {timestamp}"
        if default_label:
            suggested = f"Routing Plan — {timestamp} {default_label}"

        new_name, ok = QInputDialog.getText(
            self.dock_widget,
            "Archive Route",
            "Group name (current route will be preserved, next compute creates new group):",
            text=suggested,
        )
        if not ok or not new_name.strip():
            return

        group.setName(new_name.strip())
        self.iface.messageBar().pushSuccess(
            "Routing Plan",
            f"Route archived as '{new_name.strip()}'. Next Compute Route will create a fresh group.",
        )

    def _on_clear_route(self):
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

        self.dock_widget.hide()
        self._last_response = None
        self._route_layer = None
        self._maneuvers_layer = None

    def unload(self):
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()
            self.dock_widget = None

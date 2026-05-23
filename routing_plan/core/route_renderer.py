from .valhalla_client import decode_polyline6

ROUTE_COLOR = "#1a73e8"
ROUTE_WIDTH = 2.0
ROUTE_OPACITY = 0.85
MANEUVER_RADIUS = 1.5
MANEUVER_FILL = "#ffffff"
MANEUVER_STROKE = "#1a73e8"
MANEUVER_STROKE_WIDTH = 1.0
MANEUVER_MAX_SCALE = 50000
LAYER_GROUP_NAME = "Routing Plan"

SKIP_MANEUVER_TYPES = {0, 8, 9, 24, 25, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37}

LEG_COLORS = [
    "#1a73e8", "#188038", "#f29900", "#9334e6",
    "#d93025", "#129eaf", "#a8323a", "#e8710a",
    "#5f6368",
]

STOP_START_COLOR = "#188038"
STOP_END_COLOR = "#d93025"
STOP_MID_COLOR = "#1a73e8"
STOP_START_END_RADIUS = 8.0
STOP_MID_RADIUS = 6.0
STOP_STROKE_COLOR = "#ffffff"
STOP_STROKE_WIDTH = 1.5


def build_route_layer(response, crs="EPSG:4326"):
    from qgis.core import (
        QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
        QgsPointXY, QgsProject, QgsLayerTreeGroup,
    )
    from qgis.PyQt.QtCore import QVariant

    legs = response.get("trip", {}).get("legs", [])
    units = response.get("trip", {}).get("units", "kilometers")

    layer = QgsVectorLayer(
        f"LineString?crs={crs}&field=leg_index:integer"
        f"&field=summary:string"
        f"&field=distance_km:double"
        f"&field=duration_min:double",
        "Route",
        "memory",
    )

    pr = layer.dataProvider()
    for i, leg in enumerate(legs):
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        if not coords:
            continue
        points = [QgsPointXY(lon, lat) for lat, lon in coords]
        geom = QgsGeometry.fromPolylineXY(points)
        feat = QgsFeature()
        feat.setGeometry(geom)
        summary = leg.get("summary", {})
        length_val = summary.get("length", 0)
        if units == "miles":
            length_val = length_val * 1.60934
        distance_km = round(length_val, 3)
        duration_min = round(summary.get("time", 0) / 60, 1)

        label_parts = []
        locs = response.get("trip", {}).get("locations", [])
        if i < len(locs):
            label_parts.append(locs[i].get("name", f"WP {i}"))
        if i + 1 < len(locs):
            label_parts.append(locs[i + 1].get("name", f"WP {i+1}"))
        leg_summary = " → ".join(label_parts) if label_parts else f"Leg {i}"

        feat.setAttributes([i, leg_summary, distance_km, duration_min])
        pr.addFeature(feat)

    layer.updateExtents()
    _apply_route_style(layer)
    _add_to_group(layer)
    return layer


def build_maneuvers_layer(response, crs="EPSG:4326"):
    from qgis.core import (
        QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
        QgsPointXY, QgsProject,
    )
    from qgis.PyQt.QtCore import QVariant

    legs = response.get("trip", {}).get("legs", [])
    units = response.get("trip", {}).get("units", "kilometers")

    layer = QgsVectorLayer(
        f"Point?crs={crs}"
        f"&field=order:integer"
        f"&field=type:integer"
        f"&field=instruction:string"
        f"&field=street_names:string"
        f"&field=distance_m:double"
        f"&field=duration_s:double"
        f"&field=leg_index:integer",
        "Maneuvers",
        "memory",
    )

    pr = layer.dataProvider()
    global_order = 0

    for leg_idx, leg in enumerate(legs):
        shape_str = leg.get("shape", "")
        coords = decode_polyline6(shape_str)
        maneuvers = leg.get("maneuvers", [])

        for m in maneuvers:
            if m.get("type") in SKIP_MANEUVER_TYPES:
                continue
            begin_idx = m.get("begin_shape_index", 0)
            if begin_idx < len(coords):
                lat, lon = coords[begin_idx]
            elif coords:
                lat, lon = coords[0]
            else:
                continue

            geom = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
            feat = QgsFeature()
            street_names = ", ".join(m.get("street_names", []))
            length_m = m.get("length", 0)
            if units == "miles":
                length_m = length_m * 1609.34
            elif units == "kilometers":
                length_m = length_m * 1000

            feat.setAttributes([
                global_order,
                m.get("type"),
                m.get("instruction", ""),
                street_names,
                round(length_m, 1),
                round(m.get("time", 0), 1),
                leg_idx,
            ])
            feat.setGeometry(geom)
            pr.addFeature(feat)
            global_order += 1

    layer.updateExtents()
    _apply_maneuver_style(layer)
    _add_to_group(layer)
    return layer


def _apply_route_style(layer):
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsLineSymbol,
        QgsSingleSymbolRenderer,
    )
    try:
        leg_count = max(layer.featureCount(), 1)
        categories = []
        for i in range(leg_count):
            color = LEG_COLORS[i % len(LEG_COLORS)]
            sym = QgsLineSymbol.createSimple({
                "color": color,
                "line_width": str(ROUTE_WIDTH),
                "capstyle": "round",
                "joinstyle": "round",
            })
            sym.setOpacity(ROUTE_OPACITY)
            categories.append(QgsRendererCategory(i, sym, f"Leg {i + 1}"))
        renderer = QgsCategorizedSymbolRenderer("leg_index", categories)
        layer.setRenderer(renderer)
    except Exception:
        symbol = QgsLineSymbol.createSimple({
            "color": ROUTE_COLOR,
            "line_width": str(ROUTE_WIDTH),
            "capstyle": "round",
            "joinstyle": "round",
        })
        symbol.setOpacity(ROUTE_OPACITY)
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def _apply_maneuver_style(layer):
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsMarkerSymbol,
        QgsSingleSymbolRenderer,
    )
    try:
        unique_legs = set()
        for f in layer.getFeatures():
            idx = f.attribute("leg_index")
            if idx is not None:
                unique_legs.add(int(idx))
        if not unique_legs:
            unique_legs = {0}
        categories = []
        for i in sorted(unique_legs):
            color = LEG_COLORS[i % len(LEG_COLORS)]
            sym = QgsMarkerSymbol.createSimple({
                "name": "circle",
                "color": color,
                "outline_color": "#ffffff",
                "outline_width": str(MANEUVER_STROKE_WIDTH),
                "size": str(MANEUVER_RADIUS),
            })
            sym.setOpacity(0.9)
            categories.append(QgsRendererCategory(i, sym, f"Leg {i + 1}"))
        renderer = QgsCategorizedSymbolRenderer("leg_index", categories)
        layer.setRenderer(renderer)
        try:
            layer.setScaleBasedVisibility(True)
            layer.setMaximumScale(1)
            layer.setMinimumScale(MANEUVER_MAX_SCALE)
        except Exception:
            pass
    except Exception:
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle",
            "color": MANEUVER_FILL,
            "outline_color": MANEUVER_STROKE,
            "outline_width": str(MANEUVER_STROKE_WIDTH),
            "size": str(MANEUVER_RADIUS),
        })
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()


def build_stops_layer(response, crs="EPSG:4326"):
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    )
    locs = response.get("trip", {}).get("locations", [])
    if not locs:
        return None
    layer = QgsVectorLayer(
        f"Point?crs={crs}"
        f"&field=order:integer"
        f"&field=name:string"
        f"&field=role:string",
        "Stops",
        "memory",
    )
    pr = layer.dataProvider()
    n = len(locs)
    for i, loc in enumerate(locs):
        if i == 0:
            role = "start"
        elif i == n - 1:
            role = "end"
        else:
            role = "mid"
        lon = loc.get("lon")
        lat = loc.get("lat")
        if lat is None or lon is None:
            continue
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        feat.setAttributes([i + 1, loc.get("name", f"WP {i + 1}"), role])
        pr.addFeature(feat)
    layer.updateExtents()
    _apply_stops_style(layer)
    _add_to_group(layer, position=0)
    return layer


def _apply_stops_style(layer):
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsMarkerSymbol,
        QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling,
        QgsMessageLog, Qgis, QgsSingleSymbolRenderer,
    )
    from qgis.PyQt.QtGui import QColor, QFont

    def _marker(color, radius, shape="circle"):
        return QgsMarkerSymbol.createSimple({
            "name": shape,
            "color": color,
            "outline_color": STOP_STROKE_COLOR,
            "outline_width": str(STOP_STROKE_WIDTH),
            "size": str(radius),
        })

    # CRITICAL: categorized renderer with fallback to single-symbol
    try:
        cats = [
            QgsRendererCategory("start", _marker(STOP_START_COLOR, STOP_START_END_RADIUS, "pentagon"), "Start"),
            QgsRendererCategory("end", _marker(STOP_END_COLOR, STOP_START_END_RADIUS, "pentagon"), "End"),
            QgsRendererCategory("mid", _marker(STOP_MID_COLOR, STOP_MID_RADIUS, "circle"), "Stop"),
        ]
        layer.setRenderer(QgsCategorizedSymbolRenderer("role", cats))
    except Exception as e:
        QgsMessageLog.logMessage(
            f"Stops categorized renderer failed, fallback to simple: {e}",
            "Routing Plan", Qgis.Warning,
        )
        layer.setRenderer(QgsSingleSymbolRenderer(_marker(STOP_MID_COLOR, STOP_MID_RADIUS)))

    # OPTIONAL: labeling (non-critical — must not crash layer creation)
    try:
        font = QFont("Sans Serif", 8)
        font.setBold(True)
        fmt = QgsTextFormat()
        fmt.setFont(font)
        fmt.setColor(QColor("#ffffff"))

        s = QgsPalLayerSettings()
        s.fieldName = "order"
        s.placement = QgsPalLayerSettings.Placement.OverPoint
        s.setFormat(fmt)

        layer.setLabeling(QgsVectorLayerSimpleLabeling(s))
        layer.setLabelsEnabled(True)
    except Exception as e:
        QgsMessageLog.logMessage(
            f"Stops labeling failed (non-fatal): {e}",
            "Routing Plan", Qgis.Warning,
        )

    layer.triggerRepaint()


def _add_to_group(layer, position=None):
    from qgis.core import QgsProject

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(LAYER_GROUP_NAME)
    if group is None:
        group = root.insertGroup(0, LAYER_GROUP_NAME)
    QgsProject.instance().addMapLayer(layer, False)
    if position is not None:
        group.insertLayer(position, layer)
    else:
        group.addLayer(layer)

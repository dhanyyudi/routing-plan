"""Build QGIS vector layers from a Valhalla isochrone GeoJSON response."""

from __future__ import annotations

from typing import Any


def build_isochrone_layer(response: dict[str, Any], name: str = "Isochrones") -> Any:
    """Convert a Valhalla ``/isochrone`` GeoJSON response into a
    QgsVectorLayer with polygon features, styled with per-feature colors
    at 40 % fill opacity.

    Returns the new memory layer (already added to the "Routing Plan" group).
    """
    from qgis.core import (
        QgsVectorLayer, QgsFeature,
        QgsFillSymbol, QgsSingleSymbolRenderer, QgsRendererCategory,
        QgsCategorizedSymbolRenderer, QgsProject, QgsMessageLog, Qgis,
    )

    features = response.get("features", [])
    if not features:
        return None

    # Decide geometry type from first feature
    first_geom_type = None
    for feat in features:
        g = feat.get("geometry", {})
        gt = g.get("type", "")
        if gt == "MultiPolygon":
            first_geom_type = "MultiPolygon"
            break
        elif gt == "Polygon":
            first_geom_type = "Polygon"
            break
        elif "Line" in gt:
            first_geom_type = "LineString"
            break

    if first_geom_type is None:
        first_geom_type = "Polygon"

    geom_wkt = first_geom_type
    layer = QgsVectorLayer(
        f"{geom_wkt}?crs=EPSG:4326&field=contour:double&field=metric:string&field=color:string",
        name, "memory",
    )

    pr = layer.dataProvider()
    for feat in features:
        geom = feat.get("geometry", {})
        props = feat.get("properties", {})
        qgs_geom = _build_geometry(geom)
        if qgs_geom is None:
            continue

        qf = QgsFeature()
        qf.setGeometry(qgs_geom)

        metric = props.get("metric", "time")
        contour_val = (props.get("time") if metric == "time" else props.get("distance")) or 0
        color = props.get("color", "40bf40")
        if color and not color.startswith("#"):
            color = "#" + color

        qf.setAttributes([contour_val, metric, color])
        pr.addFeature(qf)

    layer.updateExtents()

    # Apply categorized style on contour value + color
    try:
        categories = []
        for f in layer.getFeatures():
            cval = f.attribute("contour")
            clr = f.attribute("color") or "#40bf40"
            sym = QgsFillSymbol.createSimple({
                "color": clr,
                "outline_color": clr,
                "outline_width": "0.5",
                "style": "solid",
            })
            sym.setOpacity(0.4)
            categories.append(QgsRendererCategory(cval, sym, str(cval)))
        renderer = QgsCategorizedSymbolRenderer("contour", categories)
        layer.setRenderer(renderer)
    except Exception as e:
        QgsMessageLog.logMessage(
            f"Isochrone style fallback: {e}", "Routing Plan", Qgis.Warning,
        )
        sym = QgsFillSymbol.createSimple({
            "color": "#40bf40",
            "outline_color": "#40bf40",
            "outline_width": "0.5",
            "style": "solid",
        })
        sym.setOpacity(0.4)
        layer.setRenderer(QgsSingleSymbolRenderer(sym))

    layer.triggerRepaint()

    # Add to group
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer


def _build_geometry(geojson_geom: dict[str, Any]) -> Any:
    """Convert a GeoJSON geometry dict to a QgsGeometry."""
    from qgis.core import QgsGeometry, QgsPolygon, QgsLineString, QgsPointXY
    from qgis.core import QgsMultiPolygon, QgsMultiLineString

    geom_type = geojson_geom.get("type", "")
    coords = geojson_geom.get("coordinates", [])

    if geom_type == "MultiPolygon":
        polys = []
        for polygon_coords in coords:
            for ring_coords in polygon_coords:
                points = [QgsPointXY(lon, lat) for lon, lat in ring_coords]
                if points:
                    ring = QgsLineString(points)
                    polys.append(QgsPolygon(ring))
        if polys:
            return QgsGeometry(QgsMultiPolygon(polys))

    elif geom_type == "Polygon":
        rings = []
        for ring_coords in coords:
            points = [QgsPointXY(lon, lat) for lon, lat in ring_coords]
            if points:
                rings.append(QgsLineString(points))
        if rings:
            return QgsGeometry(QgsPolygon(rings[0]))

    elif geom_type == "MultiLineString":
        lines = []
        for line_coords in coords:
            points = [QgsPointXY(lon, lat) for lon, lat in line_coords]
            if points:
                lines.append(QgsLineString(points))
        if lines:
            return QgsGeometry(QgsMultiLineString(lines))

    elif geom_type == "LineString":
        points = [QgsPointXY(lon, lat) for lon, lat in coords]
        if points:
            return QgsGeometry(QgsLineString(points))

    return None

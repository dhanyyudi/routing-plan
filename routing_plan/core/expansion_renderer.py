"""Build QGIS vector layers from Valhalla expansion GeoJSON responses."""

from __future__ import annotations

from typing import Any


def build_expansion_layer(response: dict[str, Any]) -> Any:
    """Build a LineString memory layer from a Valhalla ``/expansion`` GeoJSON."""
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
        QgsSingleSymbolRenderer, QgsLineSymbol,
    )

    features = response.get("features", [])
    layer = QgsVectorLayer(
        "LineString?crs=EPSG:4326"
        "&field=duration:double"
        "&field=distance:double"
        "&field=cost:double"
        "&field=edge_status:string",
        "Expansion", "memory",
    )

    pr = layer.dataProvider()
    for feat in features:
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        points = [QgsPointXY(lon, lat) for lon, lat in coords]
        qgs_geom = QgsGeometry.fromPolylineXY(points)

        props = feat.get("properties", {})
        qf = QgsFeature()
        qf.setGeometry(qgs_geom)
        qf.setAttributes([
            props.get("duration"),
            props.get("distance"),
            props.get("cost"),
            props.get("edge_status", ""),
        ])
        pr.addFeature(qf)

    layer.updateExtents()

    sym = QgsLineSymbol.createSimple({
        "color": "#9334e6", "line_width": "0.8", "capstyle": "round",
    })
    sym.setOpacity(0.6)
    layer.setRenderer(QgsSingleSymbolRenderer(sym))
    layer.triggerRepaint()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer

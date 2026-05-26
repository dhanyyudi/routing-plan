"""Build QGIS layers from Valhalla /locate or OSRM /nearest responses."""

from __future__ import annotations

from typing import Any


def build_locate_point_layer(response: dict[str, Any], engine: str = "valhalla") -> Any:
    """Build a Point memory layer with snapped locations + attributes."""
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
        QgsSingleSymbolRenderer, QgsMarkerSymbol,
    )

    results = response.get("results", [])
    layer = QgsVectorLayer(
        "Point?crs=EPSG:4326"
        "&field=rank:integer"
        "&field=name:string"
        "&field=distance_m:double"
        "&field=road_class:string"
        "&field=way_ids:string",
        "Snapped Points", "memory",
    )

    pr = layer.dataProvider()
    for i, r in enumerate(results):
        lon = r.get("lon", 0)
        lat = r.get("lat", 0)
        geom = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))

        feat = QgsFeature()
        feat.setGeometry(geom)
        feat.setAttributes([
            i + 1,
            r.get("name", ""),
            r.get("distance_m", 0),
            r.get("road_class", ""),
            ", ".join(map(str, r.get("way_ids", []))),
        ])
        pr.addFeature(feat)

    layer.updateExtents()

    sym = QgsMarkerSymbol.createSimple({
        "name": "circle", "color": "#d93025", "outline_color": "#ffffff",
        "outline_width": "1.0", "size": "6.0",
    })
    layer.setRenderer(QgsSingleSymbolRenderer(sym))
    layer.triggerRepaint()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer


def build_input_marker_layer(input_lat: float, input_lon: float) -> Any:
    """Build a single Point layer for the user-clicked input location."""
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
        QgsSingleSymbolRenderer, QgsMarkerSymbol,
    )

    layer = QgsVectorLayer(
        "Point?crs=EPSG:4326&field=label:string",
        "Input Point", "memory",
    )

    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(input_lon, input_lat)))
    feat.setAttributes([f"Input ({input_lat:.6f}, {input_lon:.6f})"])
    layer.dataProvider().addFeature(feat)
    layer.updateExtents()

    sym = QgsMarkerSymbol.createSimple({
        "name": "cross", "color": "#1a73e8", "outline_color": "#ffffff",
        "outline_width": "1.0", "size": "5.0",
    })
    layer.setRenderer(QgsSingleSymbolRenderer(sym))
    layer.triggerRepaint()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer

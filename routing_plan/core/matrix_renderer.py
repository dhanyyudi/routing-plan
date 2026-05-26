"""Build QGIS vector layers from a Valhalla or OSRM matrix response."""

from __future__ import annotations

from typing import Any


def build_matrix_table(response: dict[str, Any], sources: list[Any], targets: list[Any]) -> Any:
    """Build a NoGeometry memory layer from a matrix response.

    Columns: from_index, to_index, from_name, to_name, distance_km, time_sec, time_min
    """
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsProject,
    )

    pairs = response.get("sources_to_targets", [])
    src_labels = [
        getattr(s, "name", None) or f"Src {i + 1}" for i, s in enumerate(sources)
    ]
    tgt_labels = [
        getattr(t, "name", None) or f"Tgt {j + 1}" for j, t in enumerate(targets)
    ]

    layer = QgsVectorLayer(
        "NoGeometry?crs=EPSG:4326"
        "&field=from_index:integer"
        "&field=to_index:integer"
        "&field=from_name:string"
        "&field=to_name:string"
        "&field=distance_km:double"
        "&field=time_sec:double"
        "&field=time_min:double",
        "OD Matrix", "memory",
    )

    pr = layer.dataProvider()
    for pair in pairs:
        fi = pair.get("from_index", 0)
        tj = pair.get("to_index", 0)
        time_sec = pair.get("time", 0)
        dist = pair.get("distance")
        dist_km = round(dist, 3) if dist is not None else None

        feat = QgsFeature()
        feat.setAttributes([
            fi, tj,
            src_labels[fi] if fi < len(src_labels) else "",
            tgt_labels[tj] if tj < len(tgt_labels) else "",
            dist_km,
            round(time_sec, 1) if time_sec is not None else None,
            round(time_sec / 60.0, 1) if time_sec is not None else None,
        ])
        pr.addFeature(feat)

    layer.updateExtents()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer


def build_matrix_lines(
    response: dict[str, Any], sources: list[Any], targets: list[Any],
) -> Any:
    """Build a LineString memory layer connecting origin-destination pairs."""
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
        QgsSingleSymbolRenderer, QgsLineSymbol,
    )

    pairs = response.get("sources_to_targets", [])

    layer = QgsVectorLayer(
        "LineString?crs=EPSG:4326"
        "&field=from_index:integer"
        "&field=to_index:integer"
        "&field=time_sec:double"
        "&field=time_min:double"
        "&field=distance_km:double",
        "Matrix Lines", "memory",
    )

    pr = layer.dataProvider()
    for pair in pairs:
        fi = pair.get("from_index", 0)
        tj = pair.get("to_index", 0)
        if fi >= len(sources) or tj >= len(targets):
            continue
        src = sources[fi]
        tgt = targets[tj]

        geom = QgsGeometry.fromPolylineXY([
            QgsPointXY(src.lon, src.lat),
            QgsPointXY(tgt.lon, tgt.lat),
        ])
        feat = QgsFeature()
        feat.setGeometry(geom)
        time_sec = pair.get("time", 0)
        dist = pair.get("distance")
        feat.setAttributes([
            fi, tj,
            round(time_sec, 1) if time_sec is not None else None,
            round(time_sec / 60.0, 1) if time_sec is not None else None,
            round(dist, 3) if dist is not None else None,
        ])
        pr.addFeature(feat)

    layer.updateExtents()

    symbol = QgsLineSymbol.createSimple({
        "color": "#1a73e8", "line_width": "1.0", "capstyle": "round",
    })
    symbol.setOpacity(0.5)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer

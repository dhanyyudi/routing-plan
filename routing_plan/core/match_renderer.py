"""Build QGIS vector layers from map-matching responses."""

from __future__ import annotations

from typing import Any


def build_matched_route_layer(response: dict[str, Any]) -> Any:
    """Build a route layer from a map-matching response (Valhalla trip shape)."""
    from ..core.route_renderer import build_route_layer
    return build_route_layer(response, crs="EPSG:4326")


def build_attributes_table(response: dict[str, Any]) -> Any:
    """Build a NoGeometry attribute table from Valhalla ``/trace_attributes``."""
    from qgis.core import QgsVectorLayer, QgsFeature, QgsProject

    edges = response.get("edges", [])
    layer = QgsVectorLayer(
        "NoGeometry?crs=EPSG:4326"
        "&field=edge_index:integer"
        "&field=names:string"
        "&field=road_class:string"
        "&field=speed:double"
        "&field=length_km:double",
        "Match Attributes", "memory",
    )

    pr = layer.dataProvider()
    for i, edge in enumerate(edges):
        road_class = edge.get("road_class", "")
        speed = edge.get("speed", 0)
        length = edge.get("length", 0) / 1000.0
        names = ", ".join(edge.get("names", []))

        feat = QgsFeature()
        feat.setAttributes([i, names, road_class, speed, round(length, 3)])
        pr.addFeature(feat)

    layer.updateExtents()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer

"""Build QGIS layers from Valhalla height/elevation responses."""

from __future__ import annotations

from typing import Any


def build_elevation_table(response: dict[str, Any]) -> Any:
    """Build a NoGeometry memory layer with distance_m, elevation_m columns."""
    from qgis.core import QgsVectorLayer, QgsFeature, QgsProject

    heights = response.get("range_height", [])
    layer = QgsVectorLayer(
        "NoGeometry?crs=EPSG:4326"
        "&field=distance_m:double"
        "&field=elevation_m:double",
        "Elevation", "memory",
    )

    pr = layer.dataProvider()
    for sample in heights:
        d = sample[0] if len(sample) > 0 else 0
        e = sample[1] if len(sample) > 1 else 0
        feat = QgsFeature()
        feat.setAttributes([round(d, 1), round(e, 1)])
        pr.addFeature(feat)

    layer.updateExtents()

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup("Routing Plan")
    if group is None:
        group = root.insertGroup(0, "Routing Plan")
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    return layer


def compute_elevation_stats(response: dict[str, Any]) -> dict[str, float]:
    """Compute min, max, total_ascent, total_descent from height response."""
    heights = response.get("range_height", [])
    if not heights:
        return {"min": 0, "max": 0, "total_ascent": 0, "total_descent": 0}

    elevations = [h[1] for h in heights if len(h) > 1]
    if not elevations:
        return {"min": 0, "max": 0, "total_ascent": 0, "total_descent": 0}

    min_e = min(elevations)
    max_e = max(elevations)
    ascent = 0.0
    descent = 0.0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i - 1]
        if diff > 0:
            ascent += diff
        else:
            descent += abs(diff)

    return {
        "min": round(min_e, 1),
        "max": round(max_e, 1),
        "total_ascent": round(ascent, 1),
        "total_descent": round(descent, 1),
    }

import json
import os
from string import Template
from typing import Any

from .maneuver_formatter import (
    format_distance,
    format_total_summary,
    unicode_for_maneuver_type,
)
from .valhalla_client import decode_polyline6


def export_html(response, output_path, template_path=None):
    summary = format_total_summary(response)
    legs = response.get("trip", {}).get("legs", [])
    units = response.get("trip", {}).get("units", "kilometers")

    rows = []
    for leg in legs:
        for m in leg.get("maneuvers", []):
            icon = unicode_for_maneuver_type(m.get("type", 0))
            instruction = m.get("instruction", "")
            length = m.get("length", 0)
            if units == "miles":
                length_m = length * 1609.34
            else:
                length_m = length * 1000
            dist = format_distance(length_m)
            street = ", ".join(m.get("street_names", []))
            rows.append({
                "icon": icon,
                "instruction": instruction,
                "distance": dist,
                "street": street,
            })

    if template_path and os.path.exists(template_path):
        with open(template_path, encoding="utf-8") as f:
            tpl = Template(f.read())
    else:
        tpl = Template(_DEFAULT_HTML_TEMPLATE)

    geojson_data = _build_geojson(response)

    html = tpl.safe_substitute(
        distance=summary["distance"],
        duration=summary["duration"],
        length_km=str(summary["length_km"]),
        time_min=str(summary["time_min"]),
        maneuver_rows=_build_maneuver_rows_html(rows),
        geojson_data=json.dumps(geojson_data),
        route_bounds=_get_bounds(response),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


def export_geojson(response, output_path):
    data = _build_geojson(response)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path


def export_kml(response, output_path):
    legs = response.get("trip", {}).get("legs", [])
    locs = response.get("trip", {}).get("locations", [])

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        "    <name>Routing Plan</name>",
    ]

    units = response.get("trip", {}).get("units", "kilometers")

    for i, leg in enumerate(legs):
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        coord_str = " ".join(f"{lon},{lat},0" for lat, lon in coords)

        from_name = locs[i].get("name", f"WP {i}") if i < len(locs) else f"WP {i}"
        to_name = locs[i + 1].get("name", f"WP {i + 1}") if i + 1 < len(locs) else f"WP {i + 1}"
        s = leg.get("summary", {})
        length_val = s.get("length", 0)
        if units == "miles":
            length_val = length_val * 1.60934

        lines.extend([
            "    <Placemark>",
            f"      <name>Leg {i + 1}: {from_name} → {to_name}</name>",
            f"      <description>Distance: {length_val:.2f} km | Time: {s.get('time', 0) / 60:.1f} min</description>",
            "      <LineString>",
            f"        <coordinates>{coord_str}</coordinates>",
            "      </LineString>",
            "    </Placemark>",
        ])

    for m_idx, leg in enumerate(legs):
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        for n, m in enumerate(leg.get("maneuvers", [])):
            idx = m.get("begin_shape_index", 0)
            if idx >= len(coords):
                continue
            lat, lon = coords[idx]
            lines.extend([
                "    <Placemark>",
                f"      <name>Maneuver {m_idx}_{n}: {m.get('instruction', '')}</name>",
                "      <Point>",
                f"        <coordinates>{lon},{lat},0</coordinates>",
                "      </Point>",
                "    </Placemark>",
            ])

    lines.extend([
        "  </Document>",
        "</kml>",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def export_geopackage(route_layer, maneuvers_layer, output_path):
    from qgis.core import QgsVectorFileWriter

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "route"
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        route_layer, output_path,
        route_layer.transformContext(), options,
    )
    if error[0] != 0:
        raise RuntimeError(f"Failed to write route layer: {error}")

    options.layerName = "maneuvers"
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        maneuvers_layer, output_path,
        maneuvers_layer.transformContext(), options,
    )
    if error[0] != 0:
        raise RuntimeError(f"Failed to write maneuvers layer: {error}")

    return output_path


def _build_geojson(response):
    legs = response.get("trip", {}).get("legs", [])
    locs = response.get("trip", {}).get("locations", [])
    units = response.get("trip", {}).get("units", "kilometers")

    features = []

    for i, leg in enumerate(legs):
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        geojson_coords = [[lon, lat] for lat, lon in coords]

        from_name = locs[i].get("name", f"WP {i}") if i < len(locs) else f"WP {i}"
        to_name = locs[i + 1].get("name", f"WP {i + 1}") if i + 1 < len(locs) else f"WP {i + 1}"
        s = leg.get("summary", {})
        length_val = s.get("length", 0)
        if units == "miles":
            length_val = length_val * 1.60934

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords,
            },
            "properties": {
                "leg_index": i,
                "from": from_name,
                "to": to_name,
                "distance_km": round(length_val, 3),
                "duration_min": round(s.get("time", 0) / 60, 1),
            },
        })

    for leg_idx, leg in enumerate(legs):
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        for m_idx, m in enumerate(leg.get("maneuvers", [])):
            begin = m.get("begin_shape_index", 0)
            if begin >= len(coords):
                continue
            lat, lon = coords[begin]
            length = m.get("length", 0)
            if units == "miles":
                length_m = length * 1609.34
            else:
                length_m = length * 1000
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": {
                    "order": m_idx,
                    "leg_index": leg_idx,
                    "maneuver_type": m.get("type"),
                    "instruction": m.get("instruction", ""),
                    "street_names": ", ".join(m.get("street_names", [])),
                    "distance_m": round(length_m, 1),
                    "duration_s": round(m.get("time", 0), 1),
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def _build_maneuver_rows_html(rows):
    items = []
    for r in rows:
        street_line = f'<div class="street">{r["street"]}</div>' if r["street"] else ""
        items.append(
            f'<div class="maneuver-item">'
            f'<span class="icon">{r["icon"]}</span>'
            f'<div class="maneuver-text">'
            f'<div class="instruction">{r["instruction"]}</div>'
            f'{street_line}'
            f'</div>'
            f'<span class="distance">{r["distance"]}</span>'
            f'</div>'
        )
    return "\n".join(items)


def _get_bounds(response):
    legs = response.get("trip", {}).get("legs", [])
    if not legs:
        return "[]"
    all_coords = []
    for leg in legs:
        shape = leg.get("shape", "")
        coords = decode_polyline6(shape)
        all_coords.extend(coords)
    if not all_coords:
        return "[]"
    lats = [c[0] for c in all_coords]
    lons = [c[1] for c in all_coords]
    return json.dumps([[min(lats), min(lons)], [max(lats), max(lons)]])


_DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Routing Plan — Directions</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.container { display: flex; height: 100vh; }
.sidebar { width: 380px; overflow-y: auto; border-right: 1px solid #dadce0; }
.map { flex: 1; }
.header { padding: 16px; border-bottom: 1px solid #e8eaed; position: sticky; top: 0; background: #fff; z-index: 1; }
.header h1 { font-size: 18px; color: #202124; }
.header .summary { font-size: 24px; font-weight: 700; color: #1a73e8; margin: 4px 0; }
.header .detail { font-size: 13px; color: #5f6368; }
.maneuver-list { padding: 0; }
.maneuver-item { display: flex; align-items: flex-start; padding: 12px 16px;
    border-bottom: 1px solid #f1f3f4; gap: 12px; }
.maneuver-item:hover { background: #f8f9fa; }
.maneuver-item .icon { font-size: 20px; min-width: 24px; text-align: center; }
.maneuver-item .maneuver-text { flex: 1; }
.maneuver-item .instruction { font-size: 14px; color: #202124; }
.maneuver-item .street { font-size: 12px; color: #5f6368; margin-top: 2px; }
.maneuver-item .distance { font-size: 13px; color: #5f6368; white-space: nowrap; }
</style>
</head>
<body>
<div class="container">
  <div class="sidebar">
    <div class="header">
      <h1>Routing Plan</h1>
      <div class="summary">$distance · $duration</div>
      <div class="detail">$length_km km · $time_min menit</div>
    </div>
    <div class="maneuver-list">
      $maneuver_rows
    </div>
  </div>
  <div class="map" id="map"></div>
</div>
<script>
var geojson = $geojson_data;
var bounds = $route_bounds;
var map = L.map('map').fitBounds(bounds);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
L.geoJSON(geojson, {
  style: function(feature) {
    if (feature.geometry.type === 'LineString') {
      return { color: '#1a73e8', weight: 4, opacity: 0.9 };
    }
    return { radius: 4, fillColor: '#fff', color: '#1a73e8', weight: 2, fillOpacity: 1 };
  },
  pointToLayer: function(feature, latlng) {
    return L.circleMarker(latlng, { radius: 5, fillColor: '#fff', color: '#1a73e8', weight: 2, fillOpacity: 1 });
  }
}).addTo(map);
</script>
</body>
</html>"""


def export_matrix_csv(
    response: dict[str, Any],
    sources: list[Any],
    targets: list[Any],
    output_path: str,
) -> None:
    """Export a matrix response to CSV.

    Writes columns: from_index, to_index, from_name, to_name,
    distance_km, time_sec, time_min.
    """
    import csv
    with open(output_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["from_index", "to_index", "from_name", "to_name",
                    "distance_km", "time_sec", "time_min"])
        pairs = response.get("sources_to_targets", [])
        src_names = [getattr(s, "name", None) or f"Src{i}" for i, s in enumerate(sources)]
        tgt_names = [getattr(t, "name", None) or f"Tgt{j}" for j, t in enumerate(targets)]
        for pair in pairs:
            fi = pair.get("from_index", 0)
            tj = pair.get("to_index", 0)
            time_sec = pair.get("time", 0)
            dist = pair.get("distance")
            time_min = round(time_sec / 60.0, 1) if time_sec else 0
            w.writerow([
                fi, tj,
                src_names[fi] if fi < len(src_names) else "",
                tgt_names[tj] if tj < len(tgt_names) else "",
                round(dist, 3) if dist is not None else "",
                time_sec, time_min,
            ])


def export_elevation_csv(response: dict[str, Any], output_path: str) -> None:
    """Export an elevation profile response to CSV.

    Writes columns: distance_m, elevation_m.
    """
    import csv
    heights = response.get("range_height", [])
    with open(output_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["distance_m", "elevation_m"])
        for sample in heights:
            d = sample[0] if len(sample) > 0 else 0
            e = sample[1] if len(sample) > 1 else 0
            w.writerow([round(d, 1), round(e, 1)])

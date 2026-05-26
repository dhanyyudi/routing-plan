import csv
import json
from dataclasses import dataclass
from typing import Any, Optional

LAT_ALIASES = {"lat", "latitude", "y", "lintang"}
LON_ALIASES = {"lon", "long", "longitude", "x", "bujur"}
NAME_ALIASES = {"name", "nama", "title", "label", "lokasi"}


@dataclass
class Waypoint:
    lat: float
    lon: float
    name: Optional[str] = None
    lock_role: Optional[str] = None

    def validate(self):
        errors = []
        if self.lat is None or not (-90 <= self.lat <= 90):
            errors.append(f"lat {self.lat} out of range [-90, 90]")
        if self.lon is None or not (-180 <= self.lon <= 180):
            errors.append(f"lon {self.lon} out of range [-180, 180]")
        if self.lock_role not in (None, "start", "end"):
            errors.append(f"lock_role '{self.lock_role}' invalid")
        return errors


def _guess_columns(headers):
    lat_col = lon_col = name_col = None
    for i, h in enumerate(headers):
        clean = h.strip().lower()
        if clean in LAT_ALIASES:
            lat_col = i
        elif clean in LON_ALIASES:
            lon_col = i
        elif clean in NAME_ALIASES and name_col is None:
            name_col = i
    return lat_col, lon_col, name_col


def _parse_coord(value):
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def load_csv(path, lat_col=None, lon_col=None, name_col=None):
    waypoints = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(f, dialect)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV file is empty")
    headers = rows[0]
    if lat_col is None and lon_col is None:
        lat_col, lon_col, name_col = _guess_columns(headers)
    if lat_col is None or lon_col is None:
        raise ValueError(
            "Could not determine lat/lon columns. "
            "Use column names: lat/latitude/y and lon/longitude/x"
        )
    for r_idx, row in enumerate(rows[1:], start=1):
        if not row or all(c.strip() == "" for c in row):
            continue
        try:
            lat = _parse_coord(row[lat_col])
            lon = _parse_coord(row[lon_col])
        except (IndexError, ValueError) as e:
            raise ValueError(f"Row {r_idx}: invalid coordinate — {e}")
        name = row[name_col].strip() if name_col is not None and name_col < len(row) else None
        waypoints.append(Waypoint(lat=lat, lon=lon, name=name))
    if len(waypoints) < 2:
        raise ValueError("Minimal 2 waypoints required")
    return waypoints


def load_xlsx(path, sheet=0, lat_col=None, lon_col=None, name_col=None):
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required for XLSX loading")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if isinstance(sheet, int):
        ws = wb.worksheets[sheet]
    else:
        ws = wb[sheet]
    rows = [[cell.value for cell in row] for row in ws.iter_rows()]
    wb.close()
    if not rows:
        raise ValueError("XLSX sheet is empty")
    headers = rows[0]
    headers = [str(h).strip() if h is not None else "" for h in headers]
    if lat_col is None and lon_col is None:
        lat_col, lon_col, name_col = _guess_columns(headers)
    if lat_col is None or lon_col is None:
        raise ValueError(
            "Could not determine lat/lon columns. "
            "Use column names: lat/latitude/y and lon/longitude/x"
        )
    waypoints = []
    for r_idx, row in enumerate(rows[1:], start=1):
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        try:
            lat = _parse_coord(row[lat_col])
            lon = _parse_coord(row[lon_col])
        except (IndexError, ValueError, TypeError) as e:
            raise ValueError(f"Row {r_idx}: invalid coordinate — {e}")
        name = None
        if name_col is not None and name_col < len(row) and row[name_col] is not None:
            name = str(row[name_col]).strip() or None
        waypoints.append(Waypoint(lat=lat, lon=lon, name=name))
    if len(waypoints) < 2:
        raise ValueError("Minimal 2 waypoints required")
    return waypoints


# Helper untuk extract name dari GeoJSON properties (digunakan oleh load_geojson + load_csv analog)
def _extract_name_from_props(props):
    if not props:
        return None
    for key, value in props.items():
        if key.strip().lower() in NAME_ALIASES:
            if value not in (None, ""):
                return str(value).strip() or None
    return None


def load_geojson(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    elif data.get("type") == "Point":
        coords = data.get("coordinates", [])
        if len(coords) >= 2:
            props = data.get("properties", {}) or {}
            name = _extract_name_from_props(props)
            waypoints = [Waypoint(lat=coords[1], lon=coords[0], name=name)]
            if len(waypoints) < 2:
                raise ValueError("Minimal 2 waypoints required")
            return waypoints
        raise ValueError("Invalid Point geometry")
    else:
        raise ValueError(f"Unsupported GeoJSON type: {data.get('type')}")

    waypoints = []
    for f in features:
        geom = f.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        name = _extract_name_from_props(f.get("properties", {}))
        waypoints.append(Waypoint(lat=coords[1], lon=coords[0], name=name))
    if len(waypoints) < 2:
        raise ValueError("Minimal 2 waypoints required")
    return waypoints


def load_kml(path):
    from qgis.core import QgsVectorLayer
    layer = QgsVectorLayer(path, "kml", "ogr")
    if not layer.isValid():
        raise ValueError(f"Failed to load KML: {path}")
    return _extract_from_layer(layer)


def load_from_layer(layer, name_field=None):
    from qgis.core import QgsVectorLayer
    if isinstance(layer, str):
        path = layer
        layer = QgsVectorLayer(path, "layer", "ogr")
        if not layer.isValid():
            raise ValueError(f"Failed to load layer: {path}")
    return _extract_from_layer(layer, name_field)


def _wgs84_transform(layer):
    """Return a QgsCoordinateTransform from ``layer``'s CRS to EPSG:4326,
    or ``None`` if no transform is needed (layer already in 4326).

    Critical because QGIS layers from XYZ-tile contexts are often in
    EPSG:3857 (Web Mercator metres); calling ``pt.x()`` / ``pt.y()`` on
    them gives metres, not lon/lat, which routing engines reject.
    """
    from qgis.core import (
        QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject,
    )
    src = layer.crs()
    dst = QgsCoordinateReferenceSystem("EPSG:4326")
    if not src.isValid() or src == dst:
        return None
    return QgsCoordinateTransform(src, dst, QgsProject.instance())


def _extract_from_layer(layer, name_field=None):
    waypoints = []
    fields = layer.fields()
    name_idx = None

    if name_field is not None:
        name_idx = fields.indexFromName(name_field)
        if name_idx < 0:
            name_idx = None
    else:
        for i in range(fields.count()):
            fname = fields.at(i).name().strip().lower()
            if fname in NAME_ALIASES:
                name_idx = i
                break

    xform = _wgs84_transform(layer)
    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom is None:
            continue
        if geom.type() != 0:
            centroid = geom.centroid()
        else:
            centroid = geom
        if xform is not None:
            centroid.transform(xform)
        pt = centroid.asPoint()
        name = None
        if name_idx is not None and name_idx >= 0:
            val = feature.attribute(name_idx)
            if val:
                name = str(val).strip() or None
        waypoints.append(Waypoint(lat=pt.y(), lon=pt.x(), name=name))
    if len(waypoints) < 2:
        raise ValueError("Minimal 2 waypoints required")
    return waypoints


def load_trace_from_layer(
    layer: Any, timestamp_field: str | None = None,
) -> list[dict[str, Any]]:
    """Extract coordinates from a QGIS vector layer as trace points.

    Supports point and line layer geometry types. Returns a list of
    ``{lat, lon, time?}`` dicts. If ``timestamp_field`` is provided
    and exists in the layer, each point picks up that value as
    ``time`` (UNIX seconds).

    Points are ordered by index (point layer) or vertex order (line
    layer). When ``timestamp_field`` is set, the returned list is
    also sorted by that field.
    """
    from qgis.core import QgsWkbTypes

    coords: list[dict[str, Any]] = []
    fields = layer.fields()
    ts_idx = fields.indexOf(timestamp_field) if timestamp_field else -1
    xform = _wgs84_transform(layer)

    for feat in layer.getFeatures():
        geom = feat.geometry()
        if not geom:
            continue
        if xform is not None:
            geom = type(geom)(geom)  # shallow copy so we don't mutate the layer
            geom.transform(xform)

        ts_val = feat[ts_idx] if ts_idx >= 0 else None
        geom_type = geom.type()
        point_type = QgsWkbTypes.PointGeometry
        line_type = QgsWkbTypes.LineGeometry

        if geom_type == point_type:
            pt = geom.asPoint()
            entry: dict[str, Any] = {"lat": pt.y(), "lon": pt.x()}
            if ts_val is not None:
                entry["time"] = ts_val
            coords.append(entry)
        elif geom_type == line_type:
            for v in geom.vertices():
                entry = {"lat": v.y(), "lon": v.x()}
                if ts_val is not None:
                    entry["time"] = ts_val
                coords.append(entry)

    if timestamp_field and ts_idx >= 0 and len(coords) > 1:
        coords.sort(key=lambda c: c.get("time", 0))

    return coords

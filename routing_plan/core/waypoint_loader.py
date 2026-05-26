import csv
import json
from dataclasses import dataclass
from typing import Optional

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

    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom is None:
            continue
        if geom.type() != 0:
            centroid = geom.centroid()
        else:
            centroid = geom
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

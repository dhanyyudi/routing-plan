"""Transform OSRM API responses into the Valhalla trip shape.

All public functions consume an OSRM JSON dict and return a dict that
matches the Valhalla ``trip`` response structure consumed by the
renderer, exporter, and directions dock.

OSRM is asked for ``geometries=polyline6`` so the precision matches
Valhalla. Each *step* still carries its own polyline starting from
(0,0) deltas — encoded polylines CANNOT be string-concatenated to
build a leg shape, because the second string would be interpreted
as deltas from the end of the first, producing wild jumps back
toward (0,0). We therefore decode every step polyline to lat/lon
points, drop the duplicated joining point, then re-encode the leg
as a single polyline6 string.
"""

from __future__ import annotations

from typing import Any

from .maneuver_mapper import osrm_to_valhalla_type


# ── polyline6 codec ────────────────────────────────────────────────
# Encoding: Google Polyline Algorithm Format. Precision multiplier
# 1e6 for polyline6 (vs 1e5 for polyline5). Stateless, stdlib-only.

def _decode_polyline6(encoded: str) -> list[tuple[float, float]]:
    """Decode a polyline6 string to a list of ``(lat, lon)`` tuples."""
    if not encoded:
        return []
    coords: list[tuple[float, float]] = []
    index = 0
    lat = 0
    lon = 0
    length = len(encoded)
    while index < length:
        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        result = 0
        shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlon = ~(result >> 1) if (result & 1) else (result >> 1)
        lon += dlon
        coords.append((lat / 1e6, lon / 1e6))
    return coords


def _encode_polyline6(coords: list[tuple[float, float]]) -> str:
    """Encode a list of ``(lat, lon)`` tuples to a polyline6 string."""
    if not coords:
        return ""
    parts: list[str] = []
    prev_lat = 0
    prev_lon = 0
    for lat, lon in coords:
        ilat = round(lat * 1e6)
        ilon = round(lon * 1e6)
        dlat = ilat - prev_lat
        dlon = ilon - prev_lon
        prev_lat = ilat
        prev_lon = ilon
        for d in (dlat, dlon):
            d = ~(d << 1) if d < 0 else (d << 1)
            while d >= 0x20:
                parts.append(chr((0x20 | (d & 0x1F)) + 63))
                d >>= 5
            parts.append(chr(d + 63))
    return "".join(parts)


def _build_leg_shape_and_maneuvers(steps: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Decode each step polyline, drop duplicated joining points, build
    maneuvers with correct ``begin_shape_index``, and re-encode the
    whole leg as a single polyline6 string.

    Returns ``(leg_shape_polyline6, maneuvers_list)``.
    """
    all_points: list[tuple[float, float]] = []
    maneuvers: list[dict[str, Any]] = []
    for step in steps:
        step_geom = (step.get("geometry") or "").strip()
        pts = _decode_polyline6(step_geom)
        # Each step's polyline starts at the previous step's end point.
        # Drop the duplicate so we don't render zero-length segments
        # and so begin_shape_index points to the correct vertex.
        if all_points and pts:
            pts = pts[1:]

        instruction = step.get("name", "")
        modifier = step.get("maneuver", {}).get("modifier")
        step_type = step.get("maneuver", {}).get("type", "notification")
        street_names: list[str] = [step["name"]] if step.get("name") else []
        valhalla_type = osrm_to_valhalla_type(step_type, modifier)

        maneuvers.append({
            "type": valhalla_type,
            "instruction": instruction,
            "street_names": street_names,
            "length": step.get("distance", 0) / 1000.0,
            "time": step.get("duration", 0),
            "begin_shape_index": len(all_points),
        })
        all_points.extend(pts)

    return _encode_polyline6(all_points), maneuvers


def to_valhalla_route(osrm_resp: dict[str, Any], waypoints: list[Any]) -> dict[str, Any]:
    """Build a Valhalla-shaped trip response from an OSRM ``/route`` or
    ``/trip`` response.

    ``waypoints`` is a list of waypoint objects (each with ``.lat``,
    ``.lon``, ``.name``) in the original request order so we can label
    locations the same way Valhalla would.
    """
    code = osrm_resp.get("code", "")
    if code != "Ok":
        raise ValueError(f"OSRM response code is not Ok: {code}")

    # OSRM ``/trip`` returns ``trips``, ``/route`` returns ``routes``
    routes = osrm_resp.get("routes", osrm_resp.get("trips", []))
    if not routes:
        raise ValueError("OSRM response has no routes or trips")

    route = routes[0]
    legs = route.get("legs", [])

    # Build locations array (Valhalla shape: lat, lon, name)
    locations: list[dict[str, Any]] = []
    for i, wp in enumerate(waypoints):
        name = getattr(wp, "name", None) or f"WP {i + 1}"
        locations.append({
            "lat": wp.lat,
            "lon": wp.lon,
            "name": name,
            "type": "break",
        })

    # Build Valhalla legs
    valhalla_legs: list[dict[str, Any]] = []

    for leg in legs:
        steps = leg.get("steps", [])
        leg_shape, maneuvers = _build_leg_shape_and_maneuvers(steps)

        valhalla_legs.append({
            "shape": leg_shape,
            "summary": {
                "length": leg.get("distance", 0) / 1000.0,  # m → km
                "time": leg.get("duration", 0),
                "min_lat": 0.0,
                "min_lon": 0.0,
                "max_lat": 0.0,
                "max_lon": 0.0,
            },
            "maneuvers": maneuvers,
        })

    return {
        "trip": {
            "units": "kilometers",
            "locations": locations,
            "legs": valhalla_legs,
            "summary": {
                "length": route.get("distance", 0) / 1000.0,
                "time": route.get("duration", 0),
                "min_lat": 0.0,
                "min_lon": 0.0,
                "max_lat": 0.0,
                "max_lon": 0.0,
            },
        },
        "id": "routing-plan-qgis-osrm",
    }


def to_valhalla_matrix(osrm_resp: dict[str, Any]) -> dict[str, Any]:
    """Build a Valhalla-shaped ``sources_to_targets`` response from an
    OSRM ``/table`` response.
    """
    code = osrm_resp.get("code", "")
    if code != "Ok":
        raise ValueError(f"OSRM response code is not Ok: {code}")

    durations = osrm_resp.get("durations", [])
    distances = osrm_resp.get("distances", [])

    sources_to_targets: list[dict[str, Any]] = []
    for i in range(len(durations)):
        for j in range(len(durations[i]) if i < len(durations) else 0):
            duration = durations[i][j]
            dist_val = distances[i][j] if (i < len(distances) and j < len(distances[i]) and distances[i][j] is not None) else None  # noqa: E501
            distance = dist_val / 1000.0 if dist_val is not None else None
            if duration is None:
                continue
            sources_to_targets.append({
                "from_index": i,
                "to_index": j,
                "time": duration,
                "distance": distance,
            })

    return {
        "sources": osrm_resp.get("sources", []),
        "targets": osrm_resp.get("destinations", []),
        "sources_to_targets": sources_to_targets,
        "units": "kilometers",
        "id": "routing-plan-qgis-osrm",
    }


def to_valhalla_trace(osrm_resp: dict[str, Any]) -> dict[str, Any]:
    """Build a Valhalla-shaped ``trip`` response from an OSRM ``/match``
    response.

    Picks the highest-confidence matching and normalizes to the Valhalla
    trip shape. Surfaces ``confidence`` as a top-level extra key.
    """
    code = osrm_resp.get("code", "")
    if code != "Ok":
        raise ValueError(f"OSRM response code is not Ok: {code}")

    matchings = osrm_resp.get("matchings", [])
    if not matchings:
        raise ValueError("OSRM match response has no matchings")

    # Pick highest-confidence matching
    best = matchings[0]
    best_conf = best.get("confidence", 0)
    for m in matchings[1:]:
        conf = m.get("confidence", 0)
        if conf is not None and conf > best_conf:
            best = m
            best_conf = conf

    tracepoints = osrm_resp.get("tracepoints", [])
    legs = best.get("legs", [])

    # Build locations from tracepoints
    locations: list[dict[str, Any]] = []
    for i, tp in enumerate(tracepoints):
        loc: dict[str, Any] = {
            "lat": tp.get("location", [0, 0])[1] if tp else 0,
            "lon": tp.get("location", [0, 0])[0] if tp else 0,
            "name": f"TP {i + 1}",
            "type": "break",
        }
        locations.append(loc)

    # Build legs same shape as route normalizer
    valhalla_legs: list[dict[str, Any]] = []
    for leg in legs:
        steps = leg.get("steps", [])
        leg_shape, maneuvers = _build_leg_shape_and_maneuvers(steps)

        valhalla_legs.append({
            "shape": leg_shape,
            "summary": {
                "length": best.get("distance", 0) / 1000.0,
                "time": best.get("duration", 0),
                "min_lat": 0.0,
                "min_lon": 0.0,
                "max_lat": 0.0,
                "max_lon": 0.0,
            },
            "maneuvers": maneuvers,
        })

    return {
        "trip": {
            "units": "kilometers",
            "locations": locations,
            "legs": valhalla_legs,
            "summary": {
                "length": best.get("distance", 0) / 1000.0,
                "time": best.get("duration", 0),
            },
        },
        "confidence": best_conf,
        "id": "routing-plan-qgis-osrm",
    }


def to_valhalla_locate(
    osrm_resp: dict[str, Any], input_lat: float, input_lon: float
) -> dict[str, Any]:
    """Build a Valhalla-shaped ``locate`` response from an OSRM ``/nearest``
    response.

    OSRM ``/nearest`` returns ``{code, waypoints: [{name, location: [lon, lat],
    distance, hint, nodes}, ...]}``. We map to a list of per-result dicts.
    """
    code = osrm_resp.get("code", "")
    if code != "Ok":
        raise ValueError(f"OSRM response code is not Ok: {code}")

    waypoints = osrm_resp.get("waypoints", [])
    results: list[dict[str, Any]] = []
    for wp in waypoints:
        loc = wp.get("location", [0, 0])
        results.append({
            "input_lat": input_lat,
            "input_lon": input_lon,
            "lat": loc[1] if len(loc) >= 2 else 0,
            "lon": loc[0] if len(loc) >= 2 else 0,
            "name": wp.get("name", ""),
            "distance_m": wp.get("distance", 0),
            "hint": wp.get("hint", ""),
            "way_ids": list(map(str, wp.get("nodes", []))),
        })

    return {
        "results": results,
        "id": "routing-plan-qgis-osrm",
    }

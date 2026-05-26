import json


# ── polyline6 decoder ──────────────────────────────────────────────

def decode_polyline6(encoded):
    coords, index, lat, lon = [], 0, 0, 0
    while index < len(encoded):
        for coord_idx in range(2):
            shift, result = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if coord_idx == 0:
                lat += delta
            else:
                lon += delta
        coords.append((lat / 1e6, lon / 1e6))
    return coords


# ── error classification ───────────────────────────────────────────

NO_ROUTE_CODES = {442, 444}
OUT_OF_COVERAGE_CODES = {171, 170, 154}


class ValhallaError(Exception):
    def __init__(self, kind, code, message, raw=None):
        self.kind = kind
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(message)

    def __str__(self):
        return f"[{self.kind}] {self.message} (code={self.code})"


def _classify_error(status, body):
    try:
        data = json.loads(body) if isinstance(body, (str, bytes)) else body
        code = data.get("error_code")
        msg = data.get("error", "Unknown error")
    except Exception:
        return ValhallaError("invalid", status, str(body)[:500])
    if code in NO_ROUTE_CODES:
        return ValhallaError("no_route", code, msg, data)
    if code in OUT_OF_COVERAGE_CODES:
        return ValhallaError("out_of_coverage", code, msg, data)
    return ValhallaError("invalid", code, msg, data)


# ── ValhallaClient ─────────────────────────────────────────────────

VALID_COSTING_MODES = frozenset({
    "auto", "truck", "bus", "taxi",
    "motor_scooter", "motorcycle", "bicycle", "pedestrian",
})


class ValhallaClient:
    def __init__(self, endpoint="https://valhalla.dhanypedia.it.com", timeout=60):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def route(self, waypoints, costing="auto", costing_options=None,
              directions_options=None, alternates=0, date_time=None,
              exclude_polygons=None):
        payload = self._build_payload(
            waypoints, costing, costing_options, directions_options,
            alternates, date_time, exclude_polygons,
        )
        return self._do_request("/route", payload)

    def optimized_route(self, waypoints, costing="auto", costing_options=None,
                        directions_options=None, alternates=0, date_time=None,
                        exclude_polygons=None):
        payload = self._build_payload(
            waypoints, costing, costing_options, directions_options,
            alternates, date_time, exclude_polygons,
        )
        return self._do_request("/optimized_route", payload)

    def isochrone(self, location, costing="auto", contours=None,
                  polygons=True, denoise=None, generalize=None,
                  show_locations=False, date_time=None,
                  costing_options=None):
        """Call Valhalla ``/isochrone`` and return the GeoJSON response.

        ``location`` is a dict with ``{"lat": ..., "lon": ...}``.
        ``contours`` is a list of ``{"time": N, "color": "RRGGBB"}``
        or ``{"distance": N, "color": "RRGGBB"}``.
        """
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        payload = {
            "locations": [{"lat": location["lat"], "lon": location["lon"]}],
            "costing": costing,
            "contours": contours or [{"time": 15}],
            "polygons": polygons,
            "id": "routing-plan-isochrone",
        }
        if denoise is not None:
            payload["denoise"] = denoise
        if generalize is not None and generalize > 0:
            payload["generalize"] = generalize
        if show_locations:
            payload["show_locations"] = True
        if date_time:
            payload["date_time"] = date_time
        if costing_options:
            payload["costing_options"] = costing_options
        return self._do_request("/isochrone", payload)

    def matrix(self, sources, targets, costing="auto", date_time=None,
               costing_options=None):
        """Call Valhalla ``/sources_to_targets``."""
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        src_locs = [{"lat": s.lat, "lon": s.lon} for s in sources]
        tgt_locs = [{"lat": t.lat, "lon": t.lon} for t in targets]
        payload = {
            "sources": src_locs,
            "targets": tgt_locs,
            "costing": costing,
            "id": "routing-plan-matrix",
        }
        if date_time:
            payload["date_time"] = date_time
        if costing_options:
            payload["costing_options"] = costing_options
        return self._do_request("/sources_to_targets", payload)

    def trace_route(self, shape, costing="auto", shape_match="walk_or_snap",
                    costing_options=None, filters=None):
        """Call Valhalla ``/trace_route``."""
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        payload = {
            "shape": shape,
            "costing": costing,
            "shape_match": shape_match,
            "directions_options": {"units": "kilometers"},
            "id": "routing-plan-match",
        }
        if costing_options:
            payload["costing_options"] = costing_options
        if filters:
            payload["filters"] = filters
        return self._do_request("/trace_route", payload)

    def trace_attributes(self, shape, costing="auto", shape_match="walk_or_snap",
                         filters=None, costing_options=None):
        """Call Valhalla ``/trace_attributes``."""
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        payload = {
            "shape": shape,
            "costing": costing,
            "shape_match": shape_match,
            "id": "routing-plan-match-attr",
        }
        if filters:
            payload["filters"] = filters
        else:
            payload["filters"] = {
                "attributes": [
                    "edge.names", "edge.road_class", "edge.speed", "edge.length",
                ],
                "action": "include",
            }
        if costing_options:
            payload["costing_options"] = costing_options
        return self._do_request("/trace_attributes", payload)

    def expansion(self, action="route", locations=None, sources=None, targets=None,
                  costing="auto", contours=None, skip_opposites=True, dedupe=True,
                  expansion_properties=None, costing_options=None):
        """Call Valhalla ``/expansion``."""
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        payload = {
            "action": action,
            "costing": costing,
            "skip_opposites": skip_opposites,
            "dedupe": dedupe,
            "id": "routing-plan-expansion",
        }
        if expansion_properties:
            payload["expansion_properties"] = expansion_properties
        else:
            payload["expansion_properties"] = ["duration", "distance", "cost", "edge_status"]
        if locations:
            payload["locations"] = [{"lat": w.lat, "lon": w.lon} for w in locations]
        if sources:
            payload["sources"] = [{"lat": s.lat, "lon": s.lon} for s in sources]
        if targets:
            payload["targets"] = [{"lat": t.lat, "lon": t.lon} for t in targets]
        if contours:
            payload["contours"] = contours
        if costing_options:
            payload["costing_options"] = costing_options
        return self._do_request("/expansion", payload)

    def height(self, shape=None, encoded_polyline=None, shape_format="polyline6",
               range=True, height_precision=1, resample_distance=None):
        """Call Valhalla ``/height``."""
        payload = {
            "range": range,
            "height_precision": height_precision,
            "id": "routing-plan-elevation",
        }
        if encoded_polyline:
            payload["encoded_polyline"] = encoded_polyline
            payload["shape_format"] = shape_format
        elif shape:
            payload["shape"] = shape
            payload["shape_format"] = shape_format
        if resample_distance:
            payload["resample_distance"] = resample_distance
        return self._do_request("/height", payload)

    def locate(self, locations, costing="auto", verbose=True):
        """Call Valhalla ``/locate``.

        ``locations`` is a list of ``{"lat": ..., "lon": ...}`` dicts.
        """
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        payload = {
            "locations": [{"lat": loc["lat"], "lon": loc["lon"]} for loc in locations],
            "costing": costing,
            "verbose": verbose,
            "id": "routing-plan-locate",
        }
        return self._do_request("/locate", payload)

    def _build_payload(self, waypoints, costing, costing_options,
                       directions_options, alternates, date_time,
                       exclude_polygons):
        if costing not in VALID_COSTING_MODES:
            raise ValueError(
                f"Invalid costing mode '{costing}'. "
                f"Valid: {', '.join(sorted(VALID_COSTING_MODES))}"
            )
        locs = []
        for wp in waypoints:
            loc = {"lat": wp.lat, "lon": wp.lon, "type": "break"}
            if wp.name:
                loc["name"] = wp.name
            locs.append(loc)
        payload = {
            "locations": locs,
            "costing": costing,
            "directions_options": directions_options or {
                "units": "kilometers",
                "language": "en",
                "directions_type": "instructions",
            },
            "id": "routing-plan-qgis",
        }
        if costing_options:
            payload["costing_options"] = costing_options
        if alternates:
            payload["alternates"] = alternates
        if date_time:
            payload["date_time"] = date_time
        if exclude_polygons:
            payload["exclude_polygons"] = exclude_polygons
        return payload

    def _do_request(self, path, payload):
        from qgis.PyQt.QtCore import QUrl, QByteArray
        from qgis.PyQt.QtNetwork import QNetworkRequest
        from qgis.core import QgsBlockingNetworkRequest

        url = QUrl(self.endpoint + path)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setRawHeader(b"User-Agent", b"RoutingPlanQGIS/0.2.0")
        body = QByteArray(json.dumps(payload).encode("utf-8"))

        blocking = QgsBlockingNetworkRequest()
        err_code = blocking.post(request, body)

        if err_code != 0:
            raise ValhallaError(
                "network", err_code,
                f"Network error: {blocking.errorMessage()}"
            )

        reply = blocking.reply()
        raw_body = bytes(reply.content()).decode("utf-8")
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)

        if status == 0:
            raise ValhallaError("network", -1, "No HTTP response received")

        if 200 <= status < 300:
            return json.loads(raw_body)

        raise _classify_error(status, raw_body)

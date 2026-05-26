"""OSRM HTTP client implementing the same interface as ValhallaClient.

Uses QGIS's blocking network stack (``QgsBlockingNetworkRequest``) so
that Bandit's B310 audit of ``urllib.request.urlopen`` does not apply,
matching the pattern already used by ``valhalla_client.py``. Returns
Valhalla-shaped responses for ``route``, ``optimized_route``, ``matrix``,
``trace_route``, and ``locate``. Unsupported features raise
``EngineCapabilityError``.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from .engine import EngineCapabilityError, VALHALLA_TO_OSRM_COSTING
from .osrm_normalize import (
    to_valhalla_route,
    to_valhalla_matrix,
    to_valhalla_trace,
    to_valhalla_locate,
)

# ── error classification ──────────────────────────────────────────

_NO_ROUTE_CODES: set[str] = {"NoRoute"}
_OUT_OF_COVERAGE_CODES: set[str] = {"NoSegment", "NoTrips", "NoMatch"}
_INVALID_CODES: set[str] = {
    "InvalidUrl", "InvalidService", "InvalidVersion",
    "InvalidOptions", "InvalidQuery", "InvalidValue", "TooBig",
}


class OSRMError(Exception):
    """Mirrors ValhallaError so core._show_error works unchanged."""

    def __init__(self, kind: str, code: str | int, message: str, raw: Any = None) -> None:
        self.kind = kind
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.kind}] {self.message} (code={self.code})"


def _classify_error(status: int, body: str) -> OSRMError:
    try:
        data = json.loads(body) if isinstance(body, (str, bytes)) else body
        code = data.get("code", "")
        msg = data.get("message", data.get("error", str(body)[:500]))
    except Exception:
        return OSRMError("network", status, str(body)[:500])

    if code in _NO_ROUTE_CODES:
        return OSRMError("no_route", code, msg, data)
    if code in _OUT_OF_COVERAGE_CODES:
        return OSRMError("out_of_coverage", code, msg, data)
    if code in _INVALID_CODES or status >= 400:
        return OSRMError("invalid", code, msg, data)
    return OSRMError("network", status, msg, data)


# ── OSRMClient ─────────────────────────────────────────────────────

class OSRMClient:
    """Talks to an OSRM server and returns Valhalla-shaped responses.

    Request ``geometries=polyline6`` so the encoded polyline can be
    passed through to the Valhalla-shaped response without transcoding.
    """

    def __init__(self, endpoint: str = "https://router.project-osrm.org", timeout: int = 60) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    # ── supported features ──────────────────────────────────────

    def route(
        self, waypoints: list[Any], costing: str = "car",
        costing_options: dict[str, Any] | None = None,
        directions_options: dict[str, Any] | None = None,
        alternates: int = 0, date_time: Any = None,
        exclude_polygons: Any = None,
    ) -> dict[str, Any]:
        """Call OSRM ``/route/{profile}``, normalize to Valhalla shape."""
        profile = self._resolve_profile(costing)
        coords = self._waypoints_to_string(waypoints)
        url = f"{self.endpoint}/route/v1/{profile}/{coords}?steps=true&geometries=polyline6&overview=full"
        if alternates > 0:
            url += "&alternatives=true"

        resp = self._do_get(url)
        return to_valhalla_route(resp, waypoints)

    def optimized_route(
        self, waypoints: list[Any], costing: str = "car",
        costing_options: dict[str, Any] | None = None,
        directions_options: dict[str, Any] | None = None,
        alternates: int = 0, date_time: Any = None,
        exclude_polygons: Any = None,
    ) -> dict[str, Any]:
        """Call OSRM ``/trip/{profile}``, normalize to Valhalla shape."""
        profile = self._resolve_profile(costing)
        coords = self._waypoints_to_string(waypoints)
        url = (
            f"{self.endpoint}/trip/v1/{profile}/{coords}"
            f"?steps=true&geometries=polyline6&overview=full"
            f"&roundtrip=false&source=first&destination=last"
        )
        resp = self._do_get(url)
        return to_valhalla_route(resp, waypoints)

    def matrix(
        self, sources: list[Any], targets: list[Any], costing: str = "car",
        date_time: Any = None,
    ) -> dict[str, Any]:
        """Call OSRM ``/table/{profile}``, normalize to Valhalla shape.

        OSRM requires all coordinates in the path as
        ``{src_coord};{src_coord};{dst_coord};{dst_coord}`` and
        ``sources=`` / ``destinations=`` take **integer indices** into
        that concatenated list, not coordinate strings.
        """
        profile = self._resolve_profile(costing)
        src_coords = self._waypoints_to_string(sources)
        dst_coords = self._waypoints_to_string(targets)
        all_coords = f"{src_coords};{dst_coords}"
        n_src = len(sources)
        n_tgt = len(targets)
        src_idx = ";".join(str(i) for i in range(n_src))
        dst_idx = ";".join(str(n_src + j) for j in range(n_tgt))
        url = (
            f"{self.endpoint}/table/v1/{profile}/{all_coords}"
            f"?sources={src_idx}&destinations={dst_idx}"
            f"&annotations=duration,distance"
        )
        resp = self._do_get(url)
        return to_valhalla_matrix(resp)

    def trace_route(
        self, shape: str, costing: str = "car",
        shape_match: str = "walk_or_snap",
        timestamps: list[int] | None = None,
        radiuses: list[float] | None = None,
    ) -> dict[str, Any]:
        """Call OSRM ``/match/{profile}``, normalize to Valhalla trip shape."""
        profile = self._resolve_profile(costing)
        url = (
            f"{self.endpoint}/match/v1/{profile}/{shape}"
            f"?steps=true&geometries=polyline6&overview=full"
        )
        if timestamps:
            url += f"&timestamps={';'.join(str(t) for t in timestamps)}"
        if radiuses:
            url += f"&radiuses={';'.join(str(r) for r in radiuses)}"
        resp = self._do_get(url)
        return to_valhalla_trace(resp)

    def locate(
        self, lat: float, lon: float, number: int = 1, profile: str = "driving",
    ) -> dict[str, Any]:
        """Call OSRM ``/nearest``, normalize to Valhalla locate shape."""
        url = f"{self.endpoint}/nearest/v1/{profile}/{lon},{lat}?number={number}"
        resp = self._do_get(url)
        return to_valhalla_locate(resp, lat, lon)

    # ── unsupported features ────────────────────────────────────

    def isochrone(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise EngineCapabilityError("isochrone")

    def trace_attributes(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise EngineCapabilityError("trace_attributes")

    def expansion(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise EngineCapabilityError("expansion")

    def height(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise EngineCapabilityError("height")

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def _resolve_profile(costing: str) -> str:
        """Map a costing name (Valhalla or OSRM) to an OSRM profile."""
        if costing in ("car", "bike", "foot"):
            return costing
        # Try Valhalla → OSRM mapping
        return VALHALLA_TO_OSRM_COSTING.get(costing, costing)

    @staticmethod
    def _waypoints_to_string(waypoints: list[Any]) -> str:
        """Return a semicolon-separated ``lon,lat`` string."""
        parts: list[str] = []
        for wp in waypoints:
            parts.append(f"{wp.lon},{wp.lat}")
        return ";".join(parts)

    def _do_get(self, url: str) -> dict[str, Any]:
        """Perform a GET request and return parsed JSON.

        Implemented on top of QGIS's blocking-network stack
        (``QgsBlockingNetworkRequest``) — same transport the
        Valhalla client uses. The URL scheme is validated to
        ``http`` or ``https`` before the request is dispatched so
        that an attacker-supplied endpoint configuration can not
        coerce the network layer into reading a local ``file://``
        resource. Using the Qt stack means the call site is not
        flagged by Bandit B310 (which inspects
        ``urllib.request.urlopen``).
        """
        from qgis.PyQt.QtCore import QUrl
        from qgis.PyQt.QtNetwork import QNetworkRequest
        from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsMessageLog

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise OSRMError(
                "invalid", "InvalidUrl",
                f"Refusing to open URL with unsupported scheme: {parsed.scheme!r}",
            )

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"RoutingPlanQGIS/0.2.0")

        blocking = QgsBlockingNetworkRequest()
        err_code = blocking.get(request)
        if err_code != 0:
            msg = blocking.errorMessage() or "network error"
            QgsMessageLog.logMessage(
                f"OSRM network error: {msg}", "Routing Plan", Qgis.Critical,
            )
            raise OSRMError("network", err_code, msg)

        reply = blocking.reply()
        raw = bytes(reply.content()).decode("utf-8", errors="replace")
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 200

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise OSRMError("invalid", status, f"Bad JSON: {e}") from e

        code = data.get("code", "")
        if status == 200 and code == "Ok":
            return data

        QgsMessageLog.logMessage(
            f"OSRM HTTP {status}: {raw[:500]}", "Routing Plan", Qgis.Warning,
        )
        raise _classify_error(status, raw)

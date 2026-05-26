"""Map OSRM maneuver type + modifier to Valhalla numeric maneuver type.

This is a pure-function module with no Qt or QGIS dependencies so it
can be tested in plain pytest without mocking.
"""

from __future__ import annotations


def osrm_to_valhalla_type(osrm_type: str, modifier: str | None) -> int:
    """Convert an OSRM step ``type`` + optional ``modifier`` to a Valhalla
    numeric maneuver type (0–37) compatible with
    ``maneuver_formatter.MANEUVER_TYPE_ICON``.
    """
    _type = (osrm_type or "").strip().lower()
    _mod = (modifier or "").strip().lower()

    # Two-level lookup
    row = _MAPPING.get(_type, {})
    return row.get(_mod, row.get("__default__", 0))


# ── mapping table ─────────────────────────────────────────────────

def _m(modifier: str, valhalla_type: int) -> tuple[str, int]:  # noqa: F841
    return (modifier, valhalla_type)


# Per-type dicts: {"modifier": valhalla_numeric, ..., "__default__": fallback}
_MAPPING: dict[str, dict[str, int]] = {
    "depart": {
        "__default__": 1,
    },
    "arrive": {
        "__default__": 4,
    },
    "turn": {
        "left": 16,
        "right": 11,
        "sharp left": 15,
        "sharp right": 12,
        "slight left": 17,
        "slight right": 10,
        # TODO: distinguish uturn-left (14) from uturn-right (13);
        # OSRM rarely emits a side modifier on uturns, default to 14.
        "uturn": 14,
        "__default__": 0,
    },
    "continue": {
        "__default__": 9,
    },
    "new name": {
        "__default__": 9,
    },
    "notification": {
        "__default__": 9,
    },
    "merge": {
        "__default__": 23,
    },
    "on ramp": {
        "left": 20,
        "right": 18,
        "straight": 18,
        "__default__": 18,
    },
    "off ramp": {
        "left": 20,
        "right": 18,
        "__default__": 19,
    },
    "fork": {
        "left": 17,
        "right": 10,
        "slight left": 17,
        "slight right": 10,
        "sharp left": 15,
        "sharp right": 12,
        "__default__": 17,  # default to slight-left
    },
    "end of road": {
        "left": 16,
        "right": 11,
        "__default__": 16,
    },
    "roundabout": {
        "__default__": 26,
    },
    "rotary": {
        "__default__": 26,
    },
    "exit roundabout": {
        "__default__": 27,
    },
    "exit rotary": {
        "__default__": 27,
    },
    "roundabout turn": {
        "left": 16,
        "right": 11,
        "__default__": 16,
    },
}

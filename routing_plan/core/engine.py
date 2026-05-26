"""Routing engine protocol, constants, and helpers.

Defines the informal engine interface and shared costing lists.
Both ValhallaClient and OSRMClient implement the applicable methods
from this protocol and return Valhalla-shaped responses so downstream
consumers (renderer, exporter, dock) work unchanged.
"""

from __future__ import annotations

VALHALLA_COSTINGS: list[tuple[str, str]] = [
    ("auto", "Auto"),
    ("truck", "Truck"),
    ("bus", "Bus"),
    ("taxi", "Taxi"),
    ("motor_scooter", "Motor Scooter"),
    ("motorcycle", "Motorcycle"),
    ("bicycle", "Bicycle"),
    ("pedestrian", "Pedestrian"),
]

OSRM_PROFILES: list[tuple[str, str]] = [
    ("car", "Car"),
    ("bike", "Bike"),
    ("foot", "Foot"),
]

# OSRM profile to Valhalla costing name (for display / matching)
OSRM_TO_VALHALLA_COSTING: dict[str, str] = {
    "car": "auto",
    "bike": "bicycle",
    "foot": "pedestrian",
}

# Valhalla costing → OSRM profile
VALHALLA_TO_OSRM_COSTING: dict[str, str] = {
    "auto": "car",
    "truck": "car",
    "bus": "car",
    "taxi": "car",
    "motor_scooter": "car",
    "motorcycle": "car",
    "bicycle": "bike",
    "pedestrian": "foot",
}


def costings_for(engine: str) -> list[tuple[str, str]]:
    """Return the list of (value, label) costing/profiles for the given engine."""
    if engine == "osrm":
        return list(OSRM_PROFILES)
    return list(VALHALLA_COSTINGS)


class EngineCapabilityError(NotImplementedError):
    """Raised when an engine does not support a requested feature."""

    def __init__(self, feature: str) -> None:
        super().__init__(f"{feature} not supported by this engine")

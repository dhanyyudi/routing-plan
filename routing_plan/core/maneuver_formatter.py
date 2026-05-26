import os

MANEUVER_TYPE_ICON = {
    0: "straight",        # kNone
    1: "depart",          # kStart
    2: "straight",        # kStartRight
    3: "straight",        # kStartLeft
    4: "arrive",          # kDestination
    5: "straight",        # kDestinationRight
    6: "straight",        # kDestinationLeft
    7: "straight",        # kBecomes (unused?)
    8: "straight",        # kBecomes
    9: "continue",        # kContinue
    10: "slight_right",    # kSlightRight
    11: "turn_right",      # kRight
    12: "sharp_right",     # kSharpRight
    13: "uturn_right",     # kUturnRight
    14: "uturn_left",      # kUturnLeft
    15: "sharp_left",      # kSharpLeft
    16: "turn_left",       # kLeft
    17: "slight_left",     # kSlightLeft
    18: "ramp_right",      # kRampStraight
    19: "ramp_left",       # kRampRight
    20: "ramp_right",      # kRampLeft
    21: "ferry",           # kFerryEnter
    22: "ferry",           # kFerryExit
    23: "merge",           # kMerge
    24: "straight",        # kTransitConnectionStart
    25: "straight",        # kTransitConnectionTransfer
    26: "roundabout",      # kRoundaboutEnter
    27: "roundabout",      # kRoundaboutExit
    28: "straight",        # kTransitConnectionDestination
    29: "straight",        # kTransit
    30: "straight",        # kPostTransitConnection
    31: "straight",        # kPostTransitConnectionDestination
    32: "straight",        # kPostTransitContinue
    33: "straight",        # kPostTransitConnectionRamp
    34: "straight",        # kTransitPlatformEnter
    35: "straight",        # kTransitPlatformExit
    36: "straight",        # kTransitStationEnter
    37: "straight",        # kTransitStationExit
}

MANEUVER_UNICODE = {
    "depart": "⬆",
    "arrive": "🏁",
    "straight": "⬆",
    "continue": "⬆",
    "turn_left": "↰",
    "turn_right": "↱",
    "slight_left": "↖",
    "slight_right": "↗",
    "sharp_left": "⤺",
    "sharp_right": "⤻",
    "uturn_left": "↶",
    "uturn_right": "↷",
    "roundabout": "↺",
    "ramp_left": "↖",
    "ramp_right": "↗",
    "merge": "⤴",
    "ferry": "⛴",
}

ICON_NAMES = {
    "depart": "maneuver_depart",
    "arrive": "maneuver_arrive",
    "straight": "maneuver_straight",
    "continue": "maneuver_straight",
    "turn_left": "maneuver_turn_left",
    "turn_right": "maneuver_turn_right",
    "slight_left": "maneuver_slight_left",
    "slight_right": "maneuver_slight_right",
    "sharp_left": "maneuver_sharp_left",
    "sharp_right": "maneuver_sharp_right",
    "uturn_left": "maneuver_uturn_left",
    "uturn_right": "maneuver_uturn_right",
    "roundabout": "maneuver_roundabout",
    "ramp_left": "maneuver_ramp_left",
    "ramp_right": "maneuver_ramp_right",
    "merge": "maneuver_merge",
    "ferry": "maneuver_ferry",
}


def icon_for_maneuver_type(maneuver_type):
    icon_key = MANEUVER_TYPE_ICON.get(maneuver_type, "straight")
    return ICON_NAMES.get(icon_key, "maneuver_straight")


def unicode_for_maneuver_type(maneuver_type):
    icon_key = MANEUVER_TYPE_ICON.get(maneuver_type, "straight")
    return MANEUVER_UNICODE.get(icon_key, "⬆")


_ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "icons", "maneuvers_png")


def icon_path_for_maneuver_type(maneuver_type):
    icon_name = icon_for_maneuver_type(maneuver_type)
    path = os.path.join(_ICONS_DIR, f"{icon_name}.png")
    if os.path.exists(path):
        return path
    return None


def format_distance(meters):
    if meters is None or meters < 0:
        return ""
    if meters < 10:
        return f"{int(meters)} m"
    if meters < 1000:
        return f"{int(meters)} m"
    if meters < 10000:
        km = meters / 1000
        return f"{km:.1f} km".replace(".", ",")
    km = meters / 1000
    formatted = f"{km:,.0f}".replace(",", ".")
    return f"{formatted} km"


def format_duration(seconds):
    if seconds is None or seconds < 0:
        return ""
    if seconds < 60:
        return f"{int(seconds)} detik"
    if seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} menit"
    hours = seconds // 3600
    minutes = int((seconds % 3600) // 60)
    if minutes == 0:
        return f"{int(hours)} jam"
    return f"{int(hours)} j {minutes} m"


def format_total_summary(response):
    summary = response.get("trip", {}).get("summary", {})
    units = response.get("trip", {}).get("units", "kilometers")
    length = summary.get("length", 0)
    time_s = summary.get("time", 0)
    if units == "miles":
        length_m = length * 1609.34
    else:
        length_m = length * 1000
    return {
        "distance": format_distance(length_m),
        "duration": format_duration(time_s),
        "length_km": round(length, 2),
        "time_min": round(time_s / 60, 1),
    }


# ── Client-side Indonesian translation ──────────────────────────
# Valhalla server doesn't support 'id' locale. We translate English
# instructions to Indonesian client-side using regex patterns.

_TRANSLATION_RULES = [
    (r"^Turn left onto ", "Belok kiri ke "),
    (r"^Turn right onto ", "Belok kanan ke "),
    (r"^Turn left to stay on ", "Belok kiri untuk tetap di "),
    (r"^Turn right to stay on ", "Belok kanan untuk tetap di "),
    (r"^Turn left\.", "Belok kiri."),
    (r"^Turn right\.", "Belok kanan."),
    (r"^Turn left", "Belok kiri"),
    (r"^Turn right", "Belok kanan"),
    (r"^Bear left onto ", "Serong kiri ke "),
    (r"^Bear right onto ", "Serong kanan ke "),
    (r"^Bear left\.", "Serong kiri."),
    (r"^Bear right\.", "Serong kanan."),
    (r"^Bear left", "Serong kiri"),
    (r"^Bear right", "Serong kanan"),
    (r"^Sharp left onto ", "Belok tajam kiri ke "),
    (r"^Sharp right onto ", "Belok tajam kanan ke "),
    (r"^Sharp left\.", "Belok tajam kiri."),
    (r"^Sharp right\.", "Belok tajam kanan."),
    (r"^Sharp left", "Belok tajam kiri"),
    (r"^Sharp right", "Belok tajam kanan"),
    (r"^Slight left onto ", "Sedikit kiri ke "),
    (r"^Slight right onto ", "Sedikit kanan ke "),
    (r"^Slight left\.", "Sedikit kiri."),
    (r"^Slight right\.", "Sedikit kanan."),
    (r"^Slight left", "Sedikit kiri"),
    (r"^Slight right", "Sedikit kanan"),
    (r"^Continue on ", "Lanjut di "),
    (r"^Continue\.", "Lanjut."),
    (r"^Continue", "Lanjut"),
    (r"^Keep left onto ", "Tetap kiri ke "),
    (r"^Keep right onto ", "Tetap kanan ke "),
    (r"^Keep left\.", "Tetap kiri."),
    (r"^Keep right\.", "Tetap kanan."),
    (r"^Keep left", "Tetap kiri"),
    (r"^Keep right", "Tetap kanan"),
    (r"^Merge left onto ", "Bergabung kiri ke "),
    (r"^Merge right onto ", "Bergabung kanan ke "),
    (r"^Merge onto ", "Bergabung ke "),
    (r"^Merge left\.", "Bergabung kiri."),
    (r"^Merge right\.", "Bergabung kanan."),
    (r"^Merge\.", "Bergabung."),
    (r"^Merge", "Bergabung"),
    (r"^Take the ramp on the right onto ", "Ambil ramp kanan ke "),
    (r"^Take the ramp on the left onto ", "Ambil ramp kiri ke "),
    (r"^Take the ramp on the right\.", "Ambil ramp di kanan."),
    (r"^Take the ramp on the left\.", "Ambil ramp di kiri."),
    (r"^Take the ramp\.", "Ambil ramp."),
    (r"^Take the ramp", "Ambil ramp"),
    (r"^Enter the roundabout and take the 1st exit", "Masuk bundaran, ambil jalan keluar ke-1"),
    (r"^Enter the roundabout and take the 2nd exit", "Masuk bundaran, ambil jalan keluar ke-2"),
    (r"^Enter the roundabout and take the 3rd exit", "Masuk bundaran, ambil jalan keluar ke-3"),
    (r"^Enter the roundabout and take the 4th exit", "Masuk bundaran, ambil jalan keluar ke-4"),
    (r"^Enter the roundabout and take the 5th exit", "Masuk bundaran, ambil jalan keluar ke-5"),
    (r"^Enter the roundabout and take the (\d+)th exit", "Masuk bundaran, ambil jalan keluar ke-\\1"),
    (r"^Enter the roundabout\.", "Masuk bundaran."),
    (r"^Enter the roundabout", "Masuk bundaran"),
    (r"^Exit the roundabout onto ", "Keluar bundaran ke "),
    (r"^Exit the roundabout\.", "Keluar bundaran."),
    (r"^Exit the roundabout", "Keluar bundaran"),
    (r"^Take the ferry onto ", "Naik ferry ke "),
    (r"^Take the ferry\.", "Naik ferry."),
    (r"^Take the ferry", "Naik ferry"),
    (r"^You have arrived at your destination\.", "Anda telah tiba di tujuan."),
    (r"^You have arrived at your (\d+)st destination\.", "Anda telah tiba di tujuan ke-\\1."),
    (r"^You have arrived at your (\d+)nd destination\.", "Anda telah tiba di tujuan ke-\\1."),
    (r"^You have arrived at your (\d+)rd destination\.", "Anda telah tiba di tujuan ke-\\1."),
    (r"^You have arrived at your (\d+)th destination\.", "Anda telah tiba di tujuan ke-\\1."),
    (r"^You have arrived\.", "Anda telah tiba."),
    (r"^You will arrive", "Anda akan tiba"),
    (r"^Arrive at your destination\.", "Tiba di tujuan."),
    (r"\. Then ", ". Lalu "),
    (r"^You have arrived at ", "Anda telah tiba di "),
    (r"^Head ", "Menuju "),
    (r"^Start on ", "Mulai di "),
    (r"^Go north onto ", "Ke utara ke "),
    (r"^Go south onto ", "Ke selatan ke "),
    (r"^Go east onto ", "Ke timur ke "),
    (r"^Go west onto ", "Ke barat ke "),
    (r"^Go northwest onto ", "Ke barat laut ke "),
    (r"^Go northeast onto ", "Ke timur laut ke "),
    (r"^Go southwest onto ", "Ke barat daya ke "),
    (r"^Go southeast onto ", "Ke tenggara ke "),
    (r"^Go north on ", "Ke utara di "),
    (r"^Go south on ", "Ke selatan di "),
    (r"^Go east on ", "Ke timur di "),
    (r"^Go west on ", "Ke barat di "),
    (r"^Go northwest on ", "Ke barat laut di "),
    (r"^Go northeast on ", "Ke timur laut di "),
    (r"^Go southwest on ", "Ke barat daya di "),
    (r"^Go southeast on ", "Ke tenggara di "),
    (r"^Go north\.", "Ke utara."),
    (r"^Go south\.", "Ke selatan."),
    (r"^Go east\.", "Ke timur."),
    (r"^Go west\.", "Ke barat."),
    (r"^Go north", "Ke utara"),
    (r"^Go south", "Ke selatan"),
    (r"^Go east", "Ke timur"),
    (r"^Go west", "Ke barat"),
    (r"^Drive north onto ", "Berkendara utara ke "),
    (r"^Drive south onto ", "Berkendara selatan ke "),
    (r"^Drive east onto ", "Berkendara timur ke "),
    (r"^Drive west onto ", "Berkendara barat ke "),
    (r"^Drive northwest onto ", "Berkendara barat laut ke "),
    (r"^Drive northeast onto ", "Berkendara timur laut ke "),
    (r"^Drive southwest onto ", "Berkendara barat daya ke "),
    (r"^Drive southeast onto ", "Berkendara tenggara ke "),
    (r"^Drive north on ", "Berkendara utara di "),
    (r"^Drive south on ", "Berkendara selatan di "),
    (r"^Drive east on ", "Berkendara timur di "),
    (r"^Drive west on ", "Berkendara barat di "),
    (r"^Drive northwest on ", "Berkendara barat laut di "),
    (r"^Drive northeast on ", "Berkendara timur laut di "),
    (r"^Drive southwest on ", "Berkendara barat daya di "),
    (r"^Drive southeast on ", "Berkendara tenggara di "),
    (r"^Drive north\.", "Berkendara ke utara."),
    (r"^Drive south\.", "Berkendara ke selatan."),
    (r"^Drive east\.", "Berkendara ke timur."),
    (r"^Drive west\.", "Berkendara ke barat."),
    (r"^Drive north", "Berkendara ke utara"),
    (r"^Drive south", "Berkendara ke selatan"),
    (r"^Drive east", "Berkendara ke timur"),
    (r"^Drive west", "Berkendara ke barat"),
    (r"^Walk north onto ", "Jalan utara ke "),
    (r"^Walk south onto ", "Jalan selatan ke "),
    (r"^Walk east onto ", "Jalan timur ke "),
    (r"^Walk west onto ", "Jalan barat ke "),
    (r"^Walk north on ", "Jalan utara di "),
    (r"^Walk south on ", "Jalan selatan di "),
    (r"^Walk east on ", "Jalan timur di "),
    (r"^Walk west on ", "Jalan barat di "),
    (r"^Walk north\.", "Jalan ke utara."),
    (r"^Walk south\.", "Jalan ke selatan."),
    (r"^Walk east\.", "Jalan ke timur."),
    (r"^Walk west\.", "Jalan ke barat."),
    (r"^Walk north", "Jalan ke utara"),
    (r"^Walk south", "Jalan ke selatan"),
    (r"^Walk east", "Jalan ke timur"),
    (r"^Walk west", "Jalan ke barat"),
]


def translate_instruction(text, lang):
    if not text or lang != "id":
        return text
    import re
    result = text
    for pattern, replacement in _TRANSLATION_RULES:
        result = re.sub(pattern, replacement, result)
        if result != text:
            break
    return result

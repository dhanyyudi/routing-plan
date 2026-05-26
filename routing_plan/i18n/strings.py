ID = {
    "directions": "Petunjuk Arah",
    "export_html": "Ekspor HTML",
    "export_pdf": "Ekspor PDF",
    "save_gpkg": "Simpan GPKG",
    "calculating_route": "Menghitung rute…",
    "cancel": "Batal",
    "route_cancelled": "Perhitungan rute dibatalkan",
    "route_failed": "Gagal menghitung rute",
    "render_failed": "Gagal merender rute",
    "no_route_title": "Rute Tidak Ditemukan",
    "no_route_message": (
        "Rute tidak ditemukan antara waypoints yang diberikan.\n\n"
        "Coba salah satu dari:\n"
        "1. Pindahkan waypoint sedikit lebih dekat ke jalan utama\n"
        "2. Ganti costing mode (mis. dari truck ke auto, atau dari "
        "pedestrian ke bicycle)\n"
        "3. Pastikan waypoint berada di area dengan akses jalan yang "
        "tersambung — hindari lokasi di tengah hutan, laut, atau pulau "
        "tanpa jembatan\n\n"
        "Detail server:\n{detail}"
    ),
    "out_of_coverage": "⚠️ Waypoint di luar coverage area. {detail}",
    "error_with_code": "❌ Error: {message} (code={code})",

    # ── Engine selector ──
    "engine_label": "Engine:",
    "engine_valhalla": "Valhalla",
    "engine_osrm": "OSRM",
    "osrm_demo_warning_title": "OSRM Public Demo",
    "osrm_demo_warning_body": (
        "Anda menggunakan server demo publik OSRM dari project OSRM.\n\n"
        "Server ini memiliki batasan rate dan hanya untuk penggunaan personal terbatas.\n"
        "Untuk penggunaan produksi, silakan host instance OSRM sendiri.\n\n"
        "Lihat: https://project-osrm.org/"
    ),
    "feature_unsupported": "{feature} tidak didukung oleh engine {engine}",

    # ── Isochrones (F2) ──
    "iso_title": "Isochrones",
    "iso_origin": "Titik Awal",
    "iso_contours_label": "Kontur",
    "iso_metric_time": "Waktu",
    "iso_metric_distance": "Jarak",
    "iso_polygons": "Polygon",
    "iso_denoise": "Denoise",
    "iso_generalize": "Generalisasi (m)",
    "iso_compute": "Hitung Isochrones",
    "iso_pick_on_map": "Pilih dari peta",
    "iso_pick_active": "Klik peta untuk memilih…",
    "iso_pick_hint": "Klik di peta untuk menetapkan titik asal isochrone.",
    "iso_pick_captured": "Titik asal: {lat}, {lon}",
    "iso_layer_name": "Isochrones",

    # ── OD Matrix (F3) ──
    "matrix_title": "OD Matrix",
    "matrix_sources": "Titik Asal",
    "matrix_targets": "Titik Tujuan",
    "matrix_unreachable": "Tidak terjangkau",
    "matrix_export_csv": "Ekspor CSV",
    "matrix_draw_lines": "Gambar garis penghubung",
    "matrix_compute": "Hitung Matrix",
    "matrix_loading": "Menghitung matrix…",
    "matrix_no_sources": "Minimal satu titik asal diperlukan",
    "matrix_no_targets": "Minimal satu titik tujuan diperlukan",
    "matrix_delete_selected": "Hapus terpilih",
    "matrix_no_selection": "Pilih baris terlebih dahulu untuk dihapus.",

    # ── Map Matching (F4) ──
    "match_title": "Map Matching",
    "match_source_layer": "Dari layer QGIS",
    "match_source_csv": "Dari file CSV",
    "match_source_polyline": "Dari encoded polyline",
    "match_shape_match": "Shape match",
    "match_compute": "Cocokkan Trace",
    "match_with_attributes": "Ambil atribut edge",
    "match_confidence": "Confidence: {conf}%",
    "match_loading": "Mencocokkan trace ke jalan…",
    "match_attributes_layer": "Atribut Match",

    # ── Expansion (F5) ──
    "exp_title": "Expansion (Debug)",
    "exp_action": "Aksi",
    "exp_skip_opposites": "Skip opposites",
    "exp_properties_label": "Properties",
    "exp_compute": "Hitung Expansion",
    "exp_loading": "Menghitung expansion…",
    "exp_layer_name": "Expansion",

    # ── Elevation (F6) ──
    "elev_title": "Profil Elevasi",
    "elev_source_route": "Rute terakhir",
    "elev_source_layer": "Dari layer garis QGIS",
    "elev_source_polyline": "Dari encoded polyline",
    "elev_resample": "Resample jarak (m)",
    "elev_compute": "Hitung Elevasi",
    "elev_ascent": "Total tanjakan",
    "elev_descent": "Total turunan",
    "elev_export_csv": "Ekspor CSV",
    "elev_loading": "Menghitung elevasi…",
    "elev_layer_name": "Elevasi",

    # ── Snap / Locate (F7) ──
    "locate_title": "Snap to Road",
    "locate_input_label": "Titik input",
    "locate_pick_on_map": "Pilih dari peta",
    "locate_pick_active": "Klik peta untuk memilih…",
    "locate_pick_hint": "Klik di peta untuk menetapkan titik.",
    "locate_pick_captured": "Titik: {lat}, {lon}",
    "locate_count": "Jumlah hasil",
    "locate_compute": "Lokasi",
    "locate_no_results": "Tidak ada jalan terdekat",
    "locate_loading": "Mencari jalan terdekat…",
    "locate_layer_name": "Titik Tersnap",
    "locate_input_layer": "Titik Input",

    "html_saved": "HTML tersimpan: {path}",
    "geojson_saved": "GeoJSON tersimpan: {path}",
    "kml_saved": "KML tersimpan: {path}",
    "gpkg_saved": "GeoPackage tersimpan: {path}",
    "export_html_failed": "Gagal ekspor HTML: {error}",
    "export_geojson_failed": "Gagal ekspor GeoJSON: {error}",
    "export_kml_failed": "Gagal ekspor KML: {error}",
    "export_gpkg_failed": "Gagal ekspor GPKG: {error}",
    "layer_not_available": "Layer rute tidak tersedia untuk ekspor",
    "settings_title": "Pengaturan Routing Plan",
    "settings_saved": "Pengaturan disimpan",
    "endpoint_url": "Endpoint URL:",
    "default_costing": "Default Costing:",
    "language": "Bahasa Instruksi:",
    "units": "Units:",
    "timeout": "Timeout:",
    "auto_clear_previous": "Auto-clear previous route before Compute",
    "privacy_notice": (
        "⚠️ Koordinat waypoint akan dikirim ke server Valhalla untuk routing.\n"
        "Pengaturan disimpan otomatis saat dialog ditutup."
    ),
    "reset_default": "Reset ke Default",
    "seconds_suffix": " detik",
    "save_as": "Simpan sebagai…",
    "html_filter": "HTML (*.html)",
    "geojson_filter": "GeoJSON (*.geojson)",
    "kml_filter": "KML (*.kml)",
    "gpkg_filter": "GeoPackage (*.gpkg)",
}

EN = {
    "directions": "Directions",
    "export_html": "Export HTML",
    "export_pdf": "Export PDF",
    "save_gpkg": "Save GPKG",
    "calculating_route": "Calculating route…",
    "cancel": "Cancel",
    "route_cancelled": "Route calculation cancelled",
    "route_failed": "Failed to compute route",
    "render_failed": "Failed to render route",
    "no_route_title": "No Route Found",
    "no_route_message": (
        "No route could be found between the given waypoints.\n\n"
        "Try one of the following:\n"
        "1. Move the waypoint slightly closer to a main road\n"
        "2. Change costing mode (e.g. from truck to auto, or from "
        "pedestrian to bicycle)\n"
        "3. Ensure waypoints are in areas with connected road access — "
        "avoid locations in the middle of forests, sea, or islands "
        "without bridges\n\n"
        "Server detail:\n{detail}"
    ),
    "out_of_coverage": "⚠️ Waypoint outside coverage area. {detail}",
    "error_with_code": "❌ Error: {message} (code={code})",
    # ── Engine selector ──
    "engine_label": "Engine:",
    "engine_valhalla": "Valhalla",
    "engine_osrm": "OSRM",
    "osrm_demo_warning_title": "OSRM Public Demo",
    "osrm_demo_warning_body": (
        "You are using the public OSRM demo server provided by the OSRM project.\n\n"
        "This server has rate limits and is intended for limited personal use only.\n"
        "For production use, please host your own OSRM instance.\n\n"
        "See: https://project-osrm.org/"
    ),
    "feature_unsupported": "{feature} is not supported by the {engine} engine",

    # ── Isochrones (F2) ──
    "iso_title": "Isochrones",
    "iso_origin": "Origin",
    "iso_contours_label": "Contours",
    "iso_metric_time": "Time",
    "iso_metric_distance": "Distance",
    "iso_polygons": "Polygons",
    "iso_denoise": "Denoise",
    "iso_generalize": "Generalize (m)",
    "iso_compute": "Compute Isochrones",
    "iso_pick_on_map": "Pick on map",
    "iso_pick_active": "Click the map to pick…",
    "iso_pick_hint": "Click the map to set the isochrone origin.",
    "iso_pick_captured": "Origin captured: {lat}, {lon}",
    "iso_layer_name": "Isochrones",

    # ── OD Matrix (F3) ──
    "matrix_title": "OD Matrix",
    "matrix_sources": "Origins",
    "matrix_targets": "Destinations",
    "matrix_unreachable": "Unreachable",
    "matrix_export_csv": "Export CSV",
    "matrix_draw_lines": "Draw connecting lines",
    "matrix_compute": "Compute Matrix",
    "matrix_loading": "Computing matrix…",
    "matrix_no_sources": "At least one origin required",
    "matrix_no_targets": "At least one destination required",
    "matrix_delete_selected": "Delete selected",
    "matrix_no_selection": "Select one or more rows first to delete.",

    # ── Map Matching (F4) ──
    "match_title": "Map Matching",
    "match_source_layer": "From QGIS layer",
    "match_source_csv": "From CSV file",
    "match_source_polyline": "From encoded polyline",
    "match_shape_match": "Shape match",
    "match_compute": "Match Trace",
    "match_with_attributes": "Fetch edge attributes",
    "match_confidence": "Confidence: {conf}%",
    "match_loading": "Matching trace to roads…",
    "match_attributes_layer": "Match Attributes",

    # ── Expansion (F5) ──
    "exp_title": "Expansion (Debug)",
    "exp_action": "Action",
    "exp_skip_opposites": "Skip opposites",
    "exp_properties_label": "Properties",
    "exp_compute": "Compute Expansion",
    "exp_loading": "Computing expansion…",
    "exp_layer_name": "Expansion",

    # ── Elevation (F6) ──
    "elev_title": "Elevation Profile",
    "elev_source_route": "Last computed route",
    "elev_source_layer": "From QGIS line layer",
    "elev_source_polyline": "From encoded polyline",
    "elev_resample": "Resample distance (m)",
    "elev_compute": "Compute Elevation",
    "elev_ascent": "Total ascent",
    "elev_descent": "Total descent",
    "elev_export_csv": "Export CSV",
    "elev_loading": "Computing elevation…",
    "elev_layer_name": "Elevation",

    # ── Snap / Locate (F7) ──
    "locate_title": "Snap to Road",
    "locate_input_label": "Input point",
    "locate_pick_on_map": "Pick on map",
    "locate_pick_active": "Click the map to pick…",
    "locate_pick_hint": "Click the map to set the point.",
    "locate_pick_captured": "Point captured: {lat}, {lon}",
    "locate_count": "Number of results",
    "locate_compute": "Locate",
    "locate_no_results": "No nearby road found",
    "locate_loading": "Locating nearest road…",
    "locate_layer_name": "Snapped Points",
    "locate_input_layer": "Input Point",

    "html_saved": "HTML saved: {path}",
    "geojson_saved": "GeoJSON saved: {path}",
    "kml_saved": "KML saved: {path}",
    "gpkg_saved": "GeoPackage saved: {path}",
    "export_html_failed": "Failed to export HTML: {error}",
    "export_geojson_failed": "Failed to export GeoJSON: {error}",
    "export_kml_failed": "Failed to export KML: {error}",
    "export_gpkg_failed": "Failed to export GPKG: {error}",
    "layer_not_available": "Route layer not available for export",
    "settings_title": "Routing Plan Settings",
    "settings_saved": "Settings saved",
    "endpoint_url": "Endpoint URL:",
    "default_costing": "Default Costing:",
    "language": "Instruction Language:",
    "units": "Units:",
    "timeout": "Timeout:",
    "auto_clear_previous": "Auto-clear previous route before Compute",
    "privacy_notice": (
        "⚠️ Waypoint coordinates will be sent to the Valhalla server for routing.\n"
        "Settings are saved automatically when the dialog closes."
    ),
    "reset_default": "Reset to Default",
    "seconds_suffix": " sec",
    "save_as": "Save as…",
    "html_filter": "HTML (*.html)",
    "geojson_filter": "GeoJSON (*.geojson)",
    "kml_filter": "KML (*.kml)",
    "gpkg_filter": "GeoPackage (*.gpkg)",
}

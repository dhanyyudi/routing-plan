# Routing Plan — QGIS Plugin

Turn-by-turn navigation and route planning using the [Valhalla](https://github.com/valhalla/valhalla) and [OSRM](https://project-osrm.org/) routing engines for **QGIS 4.0+**.

<img src="routing_plan/icons/icon.svg" width="64" height="64" alt="Routing Plan icon">

## Features

- **Load waypoints** from CSV, Excel (XLSX), GeoJSON, KML, or QGIS vector layers
- **Compute routes** with two routing engines: Valhalla (Indonesia coverage) and OSRM (global car/bike/foot)
- **8 costing modes** for Valhalla: Auto, Truck, Bus, Taxi, Motor Scooter, Motorcycle, Bicycle, Pedestrian
- **Turn-by-turn directions** dock with Google Maps-style typography and maneuver icons
- **Multi-leg route visualization** with categorized colors per segment
- **Route optimization** — reorder waypoints for shortest path
- **Avoid options** — highways, tolls, ferries, unpaved roads
- **Departure time** — "leave now", "depart at", or "arrive by"
- **Export** routes to HTML, GeoJSON, KML, GeoPackage
- **Archive** routes — preserve multiple route results as named layer groups
- **Bilingual** — English UI with optional Indonesian maneuver translation (client-side)
- **Isochrones** — reachability polygons from a point (Valhalla)
- **OD Matrix** — origin-destination time/distance tables (Valhalla + OSRM)
- **Map Matching** — snap GPS traces to road network (Valhalla + OSRM)
- **Elevation Profile** — height sampling along a route (Valhalla)
- **Snap to Road** — find nearest road segments from a point (Valhalla + OSRM)
- **Expansion** — debug search-tree visualization (Valhalla)

## Installation

### From ZIP (recommended)

1. Download `routing_plan.zip` from [Releases](https://github.com/dhanyyudi/routing-plan/releases)
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**
3. Select the downloaded ZIP file
4. Restart QGIS if prompted

### From QGIS Plugin Repository

Add custom repository URL in QGIS Plugin Manager:
```
https://raw.githubusercontent.com/dhanyyudi/routing-plan/main/plugins.xml
```

### Manual (development)

```bash
git clone git@github.com:dhanyyudi/routing-plan.git
ln -s "$(pwd)/routing-plan/routing_plan" \
  ~/Library/Application\ Support/QGIS/QGIS4/profiles/default/python/plugins/routing_plan
```

## Usage

1. Click **Routing Plan** toolbar icon or **Plugins → Routing Plan**
2. Select engine (Valhalla or OSRM) from the combo at the top
3. **Waypoints tab** — load waypoints from file or QGIS layer
4. **Costing tab** — select travel mode and configure avoid options
5. **Departure tab** — set instruction language (EN/ID) and departure time
6. Click **Compute Route** — route renders on canvas with turn-by-turn directions dock

Additional features available under **Plugins → Routing Plan**:
- **Isochrones** — draw reachable area contours from a point
- **OD Matrix** — compute time/distance between multiple origins and destinations
- **Map Matching** — snap a GPS trace to roads
- **Elevation Profile** — sample heights along a route
- **Snap to Road** — locate the nearest road segment
- **Expansion (debug)** — visualize Valhalla's search tree

## Export Formats

| Format | Description |
|---|---|
| HTML | Interactive route report with map |
| GeoJSON | Vector route data |
| KML | Google Earth compatible |
| GeoPackage | QGIS-native spatial database |

## Requirements

- **QGIS 4.0** or later (Qt6)
- **Valhalla server** — uses `https://valhalla.dhanypedia.it.com` by default, configurable in Settings
- **OSRM server** (optional) — uses `https://router.project-osrm.org` public demo by default

## Settings

Open **Plugins → Routing Plan → Settings** to configure:
- Engine preference (Valhalla / OSRM)
- Valhalla and OSRM endpoint URLs
- Default costing mode
- Instruction language
- Units (kilometers / miles)
- Request timeout
- Auto-clear previous route behavior

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Support

☕ [Buy me a coffee](https://tiptap.gg/dhanypedia/tip) — support the development of this plugin.

## Author

**Dhany Yudi Prasetyo** — [dhanyyudi.prasetyo@gmail.com](mailto:dhanyyudi.prasetyo@gmail.com)

[GitHub Repository](https://github.com/dhanyyudi/routing-plan)

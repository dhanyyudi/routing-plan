# Routing Plan — QGIS Plugin

Turn-by-turn navigation and route planning using the [Valhalla](https://github.com/valhalla/valhalla) routing engine for **QGIS 4.0+**.

<img src="routing_plan/icons/icon.svg" width="64" height="64" alt="Routing Plan icon">

## Features

- **Load waypoints** from CSV, Excel (XLSX), GeoJSON, KML, or QGIS vector layers
- **Compute routes** with 8 costing modes: Auto, Truck, Bus, Taxi, Motor Scooter, Motorcycle, Bicycle, Pedestrian
- **Turn-by-turn directions** dock with Google Maps-style typography and maneuver icons
- **Multi-leg route visualization** with categorized colors per segment
- **Route optimization** — reorder waypoints for shortest path
- **Avoid options** — highways, tolls, ferries, unpaved roads
- **Departure time** — "leave now", "depart at", or "arrive by"
- **Export** routes to HTML, GeoJSON, KML, GeoPackage
- **Archive** routes — preserve multiple route results as named layer groups
- **Bilingual** — English UI with optional Indonesian maneuver translation (client-side)

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
2. **Waypoints tab** — load waypoints from file or QGIS layer
3. **Costing tab** — select travel mode and configure avoid options
4. **Departure tab** — set instruction language (EN/ID) and departure time
5. Click **Compute Route** — route renders on canvas with turn-by-turn directions dock

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

## Settings

Open **Plugins → Routing Plan → Settings** to configure:
- Valhalla endpoint URL
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

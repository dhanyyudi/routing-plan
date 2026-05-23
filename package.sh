#!/bin/bash
# package.sh — zip routing_plan plugin untuk distribusi
# Exclude: tests/ __pycache__/ *.pyc

set -e
cd "$(dirname "$0")"

PLUGIN_DIR="routing_plan"
OUTPUT="routing_plan.zip"
VERSION=$(grep '^version=' "$PLUGIN_DIR/metadata.txt" | cut -d= -f2)
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "📦 Packaging ${PLUGIN_DIR} → ${OUTPUT}"

# Copy plugin directory to temp, excluding dev files
rsync -a --exclude='tests' --exclude='__pycache__' --exclude='*.pyc' \
    "$PLUGIN_DIR"/ "$TMPDIR/$PLUGIN_DIR/"

# Create zip from temp
rm -f "$OUTPUT"
cd "$TMPDIR"
zip -r "$OLDPWD/$OUTPUT" "$PLUGIN_DIR" -q
cd "$OLDPWD"

SIZE=$(du -h "$OUTPUT" | cut -f1)
echo "✅ Done: ${OUTPUT} (${SIZE})"

# List contents
echo ""
echo "Contents:"
unzip -l "$OUTPUT" | tail -n +4 | grep -v '^---' | grep -v 'files$'

# Generate plugins.xml
cat > plugins.xml << XMLEOF
<?xml version="1.0" encoding="UTF-8"?>
<plugins>
  <plugin name="Routing Plan" version="$VERSION">
    <description><![CDATA[
Turn-by-turn navigation plugin using Valhalla routing engine.
Load waypoints from CSV/XLSX/GeoJSON/KML, compute routes with 8 costing modes,
export to HTML/GeoJSON/KML/GeoPackage.
    ]]></description>
    <about><![CDATA[
QGIS plugin for turn-by-turn navigation using Valhalla.
Personal & community project. Built for QGIS 4.0+.
    ]]></about>
    <version>$VERSION</version>
    <qgis_minimum_version>4.0.0</qgis_minimum_version>
    <homepage>https://github.com/dhanyyudi/routing-plan</homepage>
    <file_name>routing_plan.zip</file_name>
    <author>Dhany Yudi Prasetyo</author>
    <download_url>https://github.com/dhanyyudi/routing-plan/releases/download/v$VERSION/routing_plan.zip</download_url>
  </plugin>
</plugins>
XMLEOF

echo ""
echo "✅ plugins.xml generated"

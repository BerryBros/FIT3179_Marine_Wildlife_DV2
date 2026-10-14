"""Repair DCCEEW polygon GeoJSON for Vega/D3 and clip it to an Australia-wide view.

Run from the project root:
    python scripts/repair_map_geometry.py

Inputs expected from the existing data-preparation step:
    data/bia_selected.geojson
    data/marine_parks_outer.geojson

Outputs used by the revised charts:
    data/bia_selected_vega.geojson
    data/marine_parks_outer_vega.geojson
"""
from __future__ import annotations

import json
from pathlib import Path

from shapely import make_valid, orient_polygons
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
# Mainland Australia + Tasmania and adjacent waters. This deliberately excludes distant external territories
# so the Vega projection fits the story's Australia-wide viewing window rather than the whole globe.
CLIP = box(105.0, -50.0, 165.0, 0.0)


def polygonal_only(geom):
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    if isinstance(geom, GeometryCollection):
        polys = []
        for part in geom.geoms:
            if isinstance(part, Polygon):
                polys.append(part)
            elif isinstance(part, MultiPolygon):
                polys.extend(part.geoms)
        return unary_union(polys) if polys else None
    return None


def repair_file(src_name: str, dst_name: str, simplify_tolerance: float = 0.01) -> None:
    src = DATA / src_name
    dst = DATA / dst_name
    if not src.exists():
        raise FileNotFoundError(f"Missing {src}. Keep your existing prepared data folder, then run this script again.")

    with src.open("r", encoding="utf-8") as f:
        geo = json.load(f)

    out_features = []
    skipped = 0
    for feature in geo.get("features", []):
        raw_geom = feature.get("geometry")
        if not raw_geom:
            skipped += 1
            continue
        try:
            geom = shape(raw_geom)
            if not geom.is_valid:
                geom = make_valid(geom)
            geom = geom.intersection(CLIP)
            geom = polygonal_only(geom)
            if geom is None or geom.is_empty:
                skipped += 1
                continue
            # Reduce file size without materially changing an Australia-wide map.
            geom = geom.simplify(simplify_tolerance, preserve_topology=True)
            # d3-geo/Vega spherical polygons expect exterior rings clockwise for polygons < a hemisphere.
            geom = orient_polygons(geom, exterior_cw=True)
            out_features.append({
                "type": "Feature",
                "properties": feature.get("properties", {}),
                "geometry": mapping(geom),
            })
        except Exception as exc:
            skipped += 1
            print(f"WARNING: skipped one feature from {src_name}: {exc}")

    out = {"type": "FeatureCollection", "features": out_features}
    with dst.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = dst.stat().st_size / 1024
    print(f"Wrote {dst.relative_to(ROOT)}: {len(out_features):,} features, {size_kb:,.1f} KB; skipped {skipped:,}")


def main() -> None:
    print("Repairing marine map geometry for Vega-Lite...")
    repair_file("bia_selected.geojson", "bia_selected_vega.geojson", 0.008)
    repair_file("marine_parks_outer.geojson", "marine_parks_outer_vega.geojson", 0.012)
    print("Done.")


if __name__ == "__main__":
    main()

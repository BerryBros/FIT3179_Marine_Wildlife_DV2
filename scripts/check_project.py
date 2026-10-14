"""Pre-submission structural checks for Oceans in Motion v4."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
DATA = ROOT / "data"

USED_CHARTS = [
    "01_occurrence_point_map.vl.json",
    "02_occurrence_grid_map.vl.json",
    "03_species_record_lollipop.vl.json",
    "04_conservation_status.vl.json",
    "05_threat_network.vl.json",
    "06_bia_behaviour_map.vl.json",
    "07_behaviour_heatmap.vl.json",
    "08_occurrence_polar.vl.json",
    "09_monthly_rank_bump.vl.json",
    "10_shark_control_profile.vl.json",
    "11_protection_overlap_map.vl.json",
    "12_park_zone_stacked_bar.vl.json",
]

REQUIRED_DATA = {
    "ala_points.csv": {"species", "longitude", "latitude", "year"},
    "ala_grid.csv": {"grid_lon", "grid_lat", "record_count", "species_count"},
    "ala_species_counts.csv": {"species", "record_count"},
    "conservation_status.csv": {"display_species", "status", "status_rank"},
    "threat_matrix.csv": {"species", "threat", "documented", "note"},
    "bia_selected_vega.geojson": None,
    "bia_summary.csv": {"species", "behaviour", "feature_count"},
    "ala_monthly.csv": {"species", "month", "month_num", "record_count"},
    "ala_monthly_rank.csv": {"species", "month", "month_num", "rank", "record_count"},
    "shark_control_yearly.csv": {"year", "status", "number_caught"},
    "marine_parks_outer_vega.geojson": None,
    "park_zone_areas.csv": {"network", "iucn_zone", "area_km2"},
}


def check_csv(path: Path, expected: set[str]) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])
        missing = expected - fields
        return (not missing, f"missing columns: {sorted(missing)}" if missing else "columns OK")
    except Exception as exc:
        return False, str(exc)


def check_geojson(path: Path) -> tuple[bool, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        n = len(obj.get("features", [])) if obj.get("type") == "FeatureCollection" else 0
        return (n > 0, f"{n:,} features")
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    failures = 0

    print("\nCHART SPECS")
    for name in USED_CHARTS:
        p = CHARTS / name
        try:
            with p.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            schema = obj.get("$schema", "")
            ok = "vega-lite" in schema or schema.rstrip("/").endswith("/vega/v6.json")
            print(("PASS" if ok else "FAIL"), name)
            failures += 0 if ok else 1
        except Exception as exc:
            print("FAIL", name, exc)
            failures += 1

    print("\nDATA FILES")
    for name, cols in REQUIRED_DATA.items():
        p = DATA / name
        if not p.exists():
            print("FAIL", name, "missing")
            failures += 1
            continue

        if p.suffix == ".csv":
            ok, msg = check_csv(p, cols or set())
        else:
            ok, msg = check_geojson(p)

        print(("PASS" if ok else "FAIL"), name, msg)
        failures += 0 if ok else 1

    print("\nMAP SAFETY")
    bad_refs = []
    for name in USED_CHARTS:
        text = (CHARTS / name).read_text(encoding="utf-8")
        if "states_2026.geojson" in text or "states_2026_vega.geojson" in text:
            bad_refs.append(name)

    if bad_refs:
        print("FAIL old broken ABS-state basemap references remain:", ", ".join(bad_refs))
        failures += 1
    else:
        print("PASS active maps do not depend on the broken ABS state basemap")

    print("\nIDIOM INVENTORY")
    print("Advanced, distinct idiom types used:")
    print("  1. point map")
    print("  2. proportional-symbol map")
    print("  3. bipartite network")
    print("  4. categorical polygon map")
    print("  5. heatmap")
    print("  6. radial bar")
    print("  7. bump chart")
    print("  8. layered overlay map")
    print("Supporting basic idioms: lollipop, status ladder, paired time-series, 100% stacked bar.")

    if failures:
        print(f"\nCHECK COMPLETE: {failures} issue(s) need attention.")
        raise SystemExit(1)

    print("\nCHECK COMPLETE: all structural checks passed.")


if __name__ == "__main__":
    main()

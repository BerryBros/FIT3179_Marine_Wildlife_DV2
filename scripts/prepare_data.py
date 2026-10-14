#!/usr/bin/env python3
"""Prepare compact, Vega-friendly data for FIT3179 DV2: Australia's Marine Wildlife.

Official source services used:
- DCCEEW Biologically Important Areas (BIA)
- DCCEEW Australian Marine Parks
- ABS ASGS 2026 State/Territory boundaries
- Atlas of Living Australia (ALA) occurrence CSV supplied manually by the student

The script deliberately creates small local CSV/GeoJSON files for GitHub Pages rather
than querying large live services every time the visualisation loads.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

TIMEOUT = 90
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "FIT3179-DV2-Marine-Wildlife/1.0"})

# -----------------------------------------------------------------------------
# Official source endpoints
# -----------------------------------------------------------------------------
BIA_LAYER_BASE = (
    "https://gis.environment.gov.au/gispub/rest/services/"
    "marine/BiologicallyImportantAreas/MapServer"
)
MARINE_PARKS_LAYER = (
    "https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/"
    "Australian_Marine_Parks/FeatureServer/0"
)
MARINE_PARKS_OUTER_LAYER = (
    "https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/"
    "Australian_Marine_Parks_Outer_Boundary/FeatureServer/0"
)
ABS_STATES_SERVICE = (
    "https://geo.abs.gov.au/arcgis/rest/services/ASGS2026/STE/MapServer"
)

# Reviewed/current BIA layers selected for a manageable five-species story.
# These are polygon behaviour layers in the current protected-marine-species service.
BIA_LAYERS = {
    67: {"species": "Australian sea lion", "group": "Seal", "behaviour": "Foraging"},
    73: {"species": "Humpback whale", "group": "Whale", "behaviour": "Reproduction"},
    74: {"species": "Humpback whale", "group": "Whale", "behaviour": "Resting"},
    75: {"species": "Humpback whale", "group": "Whale", "behaviour": "Migration"},
    93: {"species": "Indo-Pacific bottlenose dolphin", "group": "Dolphin", "behaviour": "Reproduction"},
    94: {"species": "Indo-Pacific bottlenose dolphin", "group": "Dolphin", "behaviour": "Foraging"},
    95: {"species": "Indo-Pacific bottlenose dolphin", "group": "Dolphin", "behaviour": "Migration"},
    104: {"species": "Green turtle", "group": "Turtle", "behaviour": "Reproduction"},
    105: {"species": "Green turtle", "group": "Turtle", "behaviour": "Resting"},
    106: {"species": "Green turtle", "group": "Turtle", "behaviour": "Foraging"},
    107: {"species": "Green turtle", "group": "Turtle", "behaviour": "Migration"},
    127: {"species": "Grey nurse shark", "group": "Shark", "behaviour": "Reproduction"},
    128: {"species": "Grey nurse shark", "group": "Shark", "behaviour": "Foraging"},
    129: {"species": "Grey nurse shark", "group": "Shark", "behaviour": "Migration"},
}

FOCAL_SPECIES = {
    "Megaptera novaeangliae": {"display": "Humpback whale", "group": "Whale"},
    "Chelonia mydas": {"display": "Green turtle", "group": "Turtle"},
    "Carcharias taurus": {"display": "Grey nurse shark", "group": "Shark"},
    "Neophoca cinerea": {"display": "Australian sea lion", "group": "Seal"},
    "Tursiops aduncus": {"display": "Indo-Pacific bottlenose dolphin", "group": "Dolphin"},
}
DISPLAY_TO_GROUP = {v["display"]: v["group"] for v in FOCAL_SPECIES.values()}
DISPLAY_NAMES = list(DISPLAY_TO_GROUP)

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

STATE_REMAP = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "SA": "South Australia",
    "WA": "Western Australia",
    "TAS": "Tasmania",
    "NT": "Northern Territory",
    "ACT": "Australian Capital Territory",
    "OTHER TERRITORIES": "Other Territories",
}

# A visualisation window centred on the Australian mainland/Tasmania.
# This is used only to keep the point-map legible, not to redefine species ranges.
POINT_MAP_BOUNDS = {"lon_min": 108.0, "lon_max": 158.0, "lat_min": -47.0, "lat_max": -8.0}
POINT_SAMPLE_PER_SPECIES = 1200


def get_json(url: str, params: Optional[dict] = None) -> dict:
    response = SESSION.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and "error" in payload:
        raise RuntimeError(f"ArcGIS error from {url}: {payload['error']}")
    return payload


def query_geojson(layer_url: str, out_fields: str = "*", max_offset: float = 0.01) -> dict:
    # maxAllowableOffset simplifies display geometry in output degrees. This is
    # appropriate for a national web map and reduces GitHub Pages download size.
    # Do not reuse this simplified geometry for precise area/intersection analysis.
    params = {
        "where": "1=1",
        "outFields": out_fields,
        "returnGeometry": "true",
        "outSR": "4326",
        "maxAllowableOffset": str(max_offset),
        "f": "geojson",
    }
    payload = get_json(f"{layer_url}/query", params)
    if payload.get("type") != "FeatureCollection":
        raise RuntimeError(f"Expected GeoJSON FeatureCollection from {layer_url}")
    return payload


def query_arcgis_attributes(layer_url: str, out_fields: str) -> List[dict]:
    """Download all attributes using pagination, without geometry."""
    meta = get_json(layer_url, {"f": "json"})
    max_count = int(meta.get("maxRecordCount") or 1000)
    rows: List[dict] = []
    offset = 0

    while True:
        params = {
            "where": "1=1",
            "outFields": out_fields,
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": max_count,
        }
        payload = get_json(f"{layer_url}/query", params)
        batch = [f.get("attributes", {}) for f in payload.get("features", [])]
        rows.extend(batch)
        if len(batch) < max_count:
            break
        offset += len(batch)
    return rows


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:.1f} KB)")


def write_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False)
    print(f"Wrote {path.relative_to(ROOT)} ({len(df):,} rows)")


# -----------------------------------------------------------------------------
# BIA
# -----------------------------------------------------------------------------
def prepare_bia() -> None:
    features: List[dict] = []
    summary_rows: List[dict] = []

    for layer_id, meta in BIA_LAYERS.items():
        url = f"{BIA_LAYER_BASE}/{layer_id}"
        print(f"Downloading BIA layer {layer_id}: {meta['species']} / {meta['behaviour']}")
        geo = query_geojson(url)
        for feature in geo.get("features", []):
            source = feature.get("properties", {}) or {}
            clean = {
                "species": meta["species"],
                "group": meta["group"],
                "behaviour": meta["behaviour"],
                "region": source.get("REGION") or source.get("Region"),
                "location": source.get("LOCATION") or source.get("Location"),
                "season": source.get("SEASON") or source.get("Season"),
                "occurrence": source.get("OCCURRENCE") or source.get("Occurrence"),
                "use_level": source.get("USE_LEVEL") or source.get("Use_Level"),
                "eco_reason": source.get("ECO_REASON") or source.get("Eco_Reason"),
                "source_layer": layer_id,
            }
            feature["properties"] = clean
            features.append(feature)
            summary_rows.append(clean)

    collection = {"type": "FeatureCollection", "features": features}
    write_json(DATA / "bia_selected.geojson", collection)

    df = pd.DataFrame(summary_rows)
    summary = (
        df.groupby(["species", "group", "behaviour"], dropna=False)
        .size()
        .reset_index(name="feature_count")
        .sort_values(["species", "behaviour"])
    )
    write_csv(DATA / "bia_summary.csv", summary)

    group_behaviour = (
        df.groupby(["group", "behaviour"], dropna=False)
        .size()
        .reset_index(name="feature_count")
        .sort_values(["group", "behaviour"])
    )
    write_csv(DATA / "bia_group_behaviour.csv", group_behaviour)

    # Treemap hierarchy: root -> animal group -> behaviour. Values exist on leaves only.
    nodes = [{"id": "Marine wildlife", "parent": "", "group": "", "behaviour": "", "value": ""}]
    for group in sorted(group_behaviour["group"].dropna().unique()):
        nodes.append({"id": group, "parent": "Marine wildlife", "group": group, "behaviour": "", "value": ""})
        subset = group_behaviour[group_behaviour["group"] == group]
        for row in subset.itertuples(index=False):
            nodes.append({
                "id": f"{group} — {row.behaviour}",
                "parent": group,
                "group": group,
                "behaviour": row.behaviour,
                "value": int(row.feature_count),
            })
    write_csv(DATA / "bia_treemap_nodes.csv", pd.DataFrame(nodes))


# -----------------------------------------------------------------------------
# Marine Parks
# -----------------------------------------------------------------------------
def prepare_marine_parks() -> None:
    print("Downloading simplified Australian Marine Parks outer boundaries")
    parks_geo = query_geojson(MARINE_PARKS_OUTER_LAYER, "NETNAME,RESNAME")
    # Keep only fields needed by Vega to reduce file size.
    cleaned_features = []
    for f in parks_geo.get("features", []):
        p = f.get("properties", {}) or {}
        f["properties"] = {
            "network": p.get("NETNAME") or p.get("NetName"),
            "park": p.get("RESNAME") or p.get("ResName"),
        }
        # Keep the mainland/Tasmania map readable. Network statistics below still use
        # the full national dataset, including remote Commonwealth marine parks.
        coords = []
        def collect(x):
            if isinstance(x, list) and len(x) >= 2 and all(isinstance(v, (int, float)) for v in x[:2]):
                coords.append((x[0], x[1]))
            elif isinstance(x, list):
                for y in x:
                    collect(y)
        collect((f.get("geometry") or {}).get("coordinates", []))
        if coords:
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            intersects_mainland_window = not (max(xs) < 108 or min(xs) > 158 or max(ys) < -47 or min(ys) > -8)
            if intersects_mainland_window:
                cleaned_features.append(f)
    parks_geo["features"] = cleaned_features
    write_json(DATA / "marine_parks_outer.geojson", parks_geo)

    print("Downloading Australian Marine Parks zoning attributes")
    attrs = query_arcgis_attributes(
        MARINE_PARKS_LAYER,
        "NETNAME,RESNAME,ZONENAME,ZONEIUCN,NATLEGEND,AREA_KM2",
    )
    parks = pd.DataFrame(attrs)
    if parks.empty:
        raise RuntimeError("Marine Parks query returned no rows")

    parks["AREA_KM2"] = pd.to_numeric(parks["AREA_KM2"], errors="coerce").fillna(0)
    parks["ZONEIUCN"] = parks["ZONEIUCN"].fillna("Not stated")
    parks["ZONENAME"] = parks["ZONENAME"].fillna("Not stated")

    zone_area = (
        parks.groupby(["NETNAME", "ZONEIUCN"], dropna=False)["AREA_KM2"]
        .sum()
        .reset_index()
        .rename(columns={"NETNAME": "network", "ZONEIUCN": "iucn_zone", "AREA_KM2": "area_km2"})
    )
    write_csv(DATA / "park_zone_areas.csv", zone_area)

    metric_rows = []
    for network, g in parks.groupby("NETNAME"):
        total = float(g["AREA_KM2"].sum())
        area_ii = float(g.loc[g["ZONEIUCN"].astype(str).str.upper() == "II", "AREA_KM2"].sum())
        area_vi = float(g.loc[g["ZONEIUCN"].astype(str).str.upper() == "VI", "AREA_KM2"].sum())
        metric_rows.append({
            "network": network,
            "total_area_km2": total,
            "park_count": int(g["RESNAME"].nunique()),
            "zone_count": int(g["ZONENAME"].nunique()),
            "pct_iucn_ii": (100 * area_ii / total) if total else 0,
            "pct_iucn_vi": (100 * area_vi / total) if total else 0,
        })
    metrics = pd.DataFrame(metric_rows)
    write_csv(DATA / "park_network_metrics.csv", metrics)

    metric_labels = [
        ("Total protected area", "total_area_km2", "km²"),
        ("Number of parks", "park_count", "parks"),
        ("Number of zone types", "zone_count", "zones"),
        ("IUCN II share", "pct_iucn_ii", "%"),
        ("IUCN VI share", "pct_iucn_vi", "%"),
    ]
    long_rows = []
    for label, col, unit in metric_labels:
        values = pd.to_numeric(metrics[col], errors="coerce")
        lo, hi = float(values.min()), float(values.max())
        denom = hi - lo
        for row in metrics.itertuples(index=False):
            actual = float(getattr(row, col))
            norm = 0.5 if denom == 0 else (actual - lo) / denom
            long_rows.append({
                "network": row.network,
                "metric": label,
                "metric_order": len([x for x in metric_labels if x[0] <= label]),
                "value_normalised": norm,
                "actual": actual,
                "unit": unit,
            })
    # Explicit stable order rather than alphabetical count above.
    order_map = {label: i + 1 for i, (label, _, _) in enumerate(metric_labels)}
    for r in long_rows:
        r["metric_order"] = order_map[r["metric"]]
    write_csv(DATA / "park_network_metrics_long.csv", pd.DataFrame(long_rows))


# -----------------------------------------------------------------------------
# ABS 2026 states
# -----------------------------------------------------------------------------
def _choose_abs_state_layer(meta: dict) -> int:
    override = os.getenv("ABS_STATE_LAYER_ID")
    if override is not None:
        return int(override)

    layers = meta.get("layers", []) or []
    # Prefer a generalised polygon layer because the whole of Australia is shown.
    candidates = []
    for layer in layers:
        name = str(layer.get("name", "")).lower()
        score = 0
        if "general" in name:
            score += 10
        if "state" in name or "territor" in name or "ste" in name:
            score += 3
        if "point" in name:
            score -= 20
        candidates.append((score, int(layer["id"]), layer.get("name", "")))
    if not candidates:
        return 0
    candidates.sort(reverse=True)
    print("ABS layer candidates:", candidates)
    return candidates[0][1]


def _first_property(props: dict, names: Iterable[str]) -> Optional[str]:
    for name in names:
        if name in props and props[name] not in (None, ""):
            return str(props[name])
    return None


def prepare_abs_states() -> None:
    print("Discovering ABS ASGS 2026 State/Territory layer")
    meta = get_json(ABS_STATES_SERVICE, {"f": "json"})
    layer_id = _choose_abs_state_layer(meta)
    print(f"Using ABS state layer ID {layer_id}")
    geo = query_geojson(f"{ABS_STATES_SERVICE}/{layer_id}")

    cleaned = []
    for f in geo.get("features", []):
        p = f.get("properties", {}) or {}
        state_name = _first_property(
            p,
            [
                "STATE_NAME_2026", "STE_NAME_2026", "STE_NAME26", "STATE_NAME26",
                "STATE_NAME", "STE_NAME21", "STE_NAME_2021",
            ],
        )
        state_code = _first_property(
            p,
            ["STATE_CODE_2026", "STE_CODE_2026", "STE_CODE26", "STATE_CODE", "STE_CODE21"],
        )
        if state_name and state_name != "Other Territories":
            cleaned.append({
                "type": "Feature",
                "geometry": f.get("geometry"),
                "properties": {"state": state_name, "state_code": state_code},
            })
    if not cleaned:
        raise RuntimeError(
            "ABS boundary service was reached but a state-name field could not be identified. "
            "Open the selected ArcGIS layer metadata and add its name field to prepare_abs_states()."
        )
    write_json(DATA / "states_2026.geojson", {"type": "FeatureCollection", "features": cleaned})


# -----------------------------------------------------------------------------
# ALA occurrence CSV
# -----------------------------------------------------------------------------
def _find_col(df: pd.DataFrame, candidates: Iterable[str], required: bool = True) -> Optional[str]:
    exact = {c: c for c in df.columns}
    lower = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name in exact:
            return exact[name]
        if name.lower() in lower:
            return lower[name.lower()]
    if required:
        raise KeyError(f"Could not find any of {list(candidates)} in ALA columns")
    return None


def _empty_ala_outputs() -> None:
    write_csv(DATA / "ala_points.csv", pd.DataFrame(columns=["species", "group", "latitude", "longitude", "year", "month_num", "state"]))
    write_csv(DATA / "ala_monthly.csv", pd.DataFrame(columns=["species", "group", "month_num", "month", "record_count"]))
    write_csv(DATA / "ala_state_species.csv", pd.DataFrame(columns=["state", "species_count", "record_count"]))
    write_csv(DATA / "ala_species_counts.csv", pd.DataFrame(columns=["species", "group", "record_count"]))


def prepare_ala() -> None:
    path = RAW / "ala_occurrences.csv"
    if not path.exists():
        print("\nWARNING: raw/ala_occurrences.csv is missing.")
        print("Download occurrence records from ALA, rename the CSV to ala_occurrences.csv, then rerun this script.\n")
        _empty_ala_outputs()
        return

    print(f"Reading {path}")
    df = pd.read_csv(path, low_memory=False)

    scientific_col = _find_col(df, ["scientificName", "scientific_name", "species"])
    common_col = _find_col(df, ["vernacularName", "commonName", "common_name", "commonNameComplete"], required=False)
    lat_col = _find_col(df, ["decimalLatitude", "latitude", "lat"])
    lon_col = _find_col(df, ["decimalLongitude", "longitude", "lon", "lng"])
    date_col = _find_col(df, ["eventDate", "event_date", "date"], required=False)
    year_col = _find_col(df, ["year"], required=False)
    month_col = _find_col(df, ["month"], required=False)
    state_col = _find_col(df, ["stateProvince", "state_province", "state", "stateTerritory"], required=False)

    scientific = df[scientific_col].astype(str).str.strip()
    common = df[common_col].astype(str).str.strip() if common_col else pd.Series("", index=df.index)

    # Prefer scientific-name matching, but keep a fallback for display-name matches.
    sci_to_display = {k.lower(): v["display"] for k, v in FOCAL_SPECIES.items()}
    display_lower = {name.lower(): name for name in DISPLAY_NAMES}

    def map_species(i: int) -> Optional[str]:
        s = scientific.iat[i].lower()
        c = common.iat[i].lower()
        if s in sci_to_display:
            return sci_to_display[s]
        if c in display_lower:
            return display_lower[c]
        return None

    species = pd.Series([map_species(i) for i in range(len(df))], index=df.index)
    keep = species.notna()
    df = df.loc[keep].copy()
    df["species"] = species.loc[keep].values
    df["group"] = df["species"].map(DISPLAY_TO_GROUP)
    df["latitude"] = pd.to_numeric(df[lat_col], errors="coerce")
    df["longitude"] = pd.to_numeric(df[lon_col], errors="coerce")

    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    else:
        dates = pd.Series(pd.NaT, index=df.index)

    if year_col:
        years = pd.to_numeric(df[year_col], errors="coerce")
        df["year"] = years.fillna(dates.dt.year)
    else:
        df["year"] = dates.dt.year

    if month_col:
        months = pd.to_numeric(df[month_col], errors="coerce")
        df["month_num"] = months.fillna(dates.dt.month)
    else:
        df["month_num"] = dates.dt.month

    if state_col:
        raw_state = df[state_col].astype(str).str.strip()
        upper = raw_state.str.upper()
        df["state"] = upper.map(STATE_REMAP).fillna(raw_state)
    else:
        df["state"] = ""

    df = df.dropna(subset=["latitude", "longitude"])
    # Broad validity checks, not a claim about species range.
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)]

    # Full filtered ALA set is used for aggregates.
    monthly = df[df["month_num"].between(1, 12)].copy()
    monthly["month_num"] = monthly["month_num"].astype(int)
    monthly_agg = (
        monthly.groupby(["species", "group", "month_num"])
        .size()
        .reset_index(name="record_count")
    )
    # Complete the 12-month grid so line/radial charts have stable month order.
    full_index = pd.MultiIndex.from_product(
        [DISPLAY_NAMES, range(1, 13)], names=["species", "month_num"]
    )
    complete = monthly_agg.set_index(["species", "month_num"])["record_count"].reindex(full_index, fill_value=0).reset_index()
    complete["group"] = complete["species"].map(DISPLAY_TO_GROUP)
    complete["month"] = complete["month_num"].map(MONTH_NAMES)
    write_csv(DATA / "ala_monthly.csv", complete[["species", "group", "month_num", "month", "record_count"]])

    species_counts = (
        df.groupby(["species", "group"]).size().reset_index(name="record_count").sort_values("record_count", ascending=False)
    )
    write_csv(DATA / "ala_species_counts.csv", species_counts)

    state_valid = df[df["state"].notna() & (df["state"] != "")]
    state_summary = (
        state_valid.groupby("state")
        .agg(species_count=("species", "nunique"), record_count=("species", "size"))
        .reset_index()
    )
    write_csv(DATA / "ala_state_species.csv", state_summary)

    # Point map: deterministic sample of records in the mainland/Tasmania viewing window.
    b = POINT_MAP_BOUNDS
    map_df = df[
        df["longitude"].between(b["lon_min"], b["lon_max"])
        & df["latitude"].between(b["lat_min"], b["lat_max"])
    ].copy()

    samples = []
    for species_name, g in map_df.groupby("species"):
        n = min(len(g), POINT_SAMPLE_PER_SPECIES)
        samples.append(g.sample(n=n, random_state=3179) if len(g) > n else g)
    points = pd.concat(samples, ignore_index=True) if samples else map_df.head(0)
    points = points[["species", "group", "latitude", "longitude", "year", "month_num", "state"]]
    write_csv(DATA / "ala_points.csv", points)


# -----------------------------------------------------------------------------
# Source manifest
# -----------------------------------------------------------------------------
def prepare_source_manifest() -> None:
    rows = [
        {
            "dataset": "Atlas of Living Australia occurrence records",
            "owner": "Atlas of Living Australia",
            "url": "https://www.ala.org.au/",
            "use": "Occurrence point map, state richness, monthly record patterns, record counts",
            "note": "Insert the DOI generated by your ALA download into index.html before submission.",
        },
        {
            "dataset": "Biologically Important Areas for protected marine species",
            "owner": "DCCEEW",
            "url": BIA_LAYER_BASE,
            "use": "Behaviour polygons, behaviour heatmap, treemap and habitat/protection overlay",
            "note": "BIAs identify areas important for behaviours; they are not full species ranges.",
        },
        {
            "dataset": "Australian Marine Parks",
            "owner": "DCCEEW / Parks Australia",
            "url": MARINE_PARKS_LAYER,
            "use": "Marine park zoning, network metrics and protected-area overlay",
            "note": "Commonwealth marine parks; not all State/Territory marine protected areas.",
        },
        {
            "dataset": "ASGS Edition 4 State and Territory boundaries (2026)",
            "owner": "Australian Bureau of Statistics",
            "url": ABS_STATES_SERVICE,
            "use": "Australia basemap and state choropleth",
            "note": "Generalised layer preferred for an Australia-wide web map.",
        },
    ]
    write_csv(DATA / "source_manifest.csv", pd.DataFrame(rows))


def main() -> None:
    print("Preparing FIT3179 DV2 marine-wildlife data...\n")
    prepare_abs_states()
    prepare_bia()
    prepare_marine_parks()
    prepare_ala()
    prepare_source_manifest()
    print("\nDone. Serve the project through a local web server; do not open index.html with file://.")


if __name__ == "__main__":
    main()

# Oceans in Motion — v4 advanced-idiom upgrade

This is a replacement pack for the visualisation code, not your raw data.

## Replace these folders/files in your existing project

1. Delete your existing `charts/` folder and replace it with this `charts/` folder.
2. Replace:
   - `index.html`
   - `css/style.css`
   - `js/main.js`
   - `scripts/check_project.py`
3. You may also replace:
   - `scripts/repair_map_geometry.py`
   - `scripts/prepare_shark_control.py`
4. Merge the two small files in `data/`:
   - `conservation_status.csv`
   - `threat_matrix.csv`
5. Keep all of your existing ALA ZIP files and generated data files.

## Required generated data that should already exist

- `data/ala_points.csv`
- `data/ala_grid.csv`
- `data/ala_species_counts.csv`
- `data/ala_monthly.csv`
- `data/ala_monthly_rank.csv`
- `data/bia_summary.csv`
- `data/bia_selected_vega.geojson`
- `data/marine_parks_outer_vega.geojson`
- `data/park_zone_areas.csv`
- `data/shark_control_yearly.csv`

If the repaired map files or shark-control file are missing:

```powershell
python scripts/repair_map_geometry.py
python scripts/prepare_shark_control.py
```

Then run:

```powershell
python scripts/check_project.py
python -m http.server 8000
```

Open `http://localhost:8000` and hard-refresh with `Ctrl + Shift + R`.

## Chart inventory

There are 12 active visualisations. Eight distinct advanced idiom types are used:
point map, proportional-symbol map, bipartite network, categorical polygon map, heatmap, radial bar, bump chart, and layered overlay map.

See `notes/IDIOM-RATIONALE.md` for the interview-ready What/Why/How rationale.
